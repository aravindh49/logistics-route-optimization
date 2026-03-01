from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import joblib
import os

from src.engines.graph_engine import get_dynamic_road_graph
from src.engines.weight_engine import apply_conditions
from src.engines.eco_engine import calculate_emission
from src.engines.optimization_engine import optimize_single_segment, optimize_multi_stop_tsp
import osmnx as ox

# --- Application Setup ---
app = FastAPI(title="Logistics Optimization API | TamilNaduAI")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="web"), name="static")

# --- Global Resources ---
resources = {
    "df": None,
}

def load_resources():
    try:
        print("Creating Resources...")
        resources["df"] = pd.read_csv("data/logistics_data.csv")
        print("✅ Resources Loaded Successfully.")
    except Exception as e:
        print(f"❌ Error loading resources: {e}")

load_resources()

# --- Data Models ---
class ScenarioSettings(BaseModel):
    heavy_rain: bool = False
    accident_zone: bool = False
    rush_hour: bool = False

class SingleOptimizationRequest(BaseModel):
    start_node: str
    end_node: str
    vehicle_type: str = "diesel"
    scenario: ScenarioSettings = ScenarioSettings()

class MultiOptimizationRequest(BaseModel):
    origin: str
    stops: list[str] = []
    destination: str
    vehicle_type: str = "diesel"
    scenario: ScenarioSettings = ScenarioSettings()

# --- Endpoints ---
@app.get("/")
async def read_index():
    return FileResponse('web/index.html')

@app.get("/cities")
def get_cities():
    df = resources["df"]
    if df is None:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    start_cities = df[['start_location', 'start_lat', 'start_lon']].rename(
        columns={'start_location': 'name', 'start_lat': 'lat', 'start_lon': 'lon'}
    )
    end_cities = df[['end_location', 'end_lat', 'end_lon']].rename(
        columns={'end_location': 'name', 'end_lat': 'lat', 'end_lon': 'lon'}
    )
    
    all_cities = pd.concat([start_cities, end_cities]).drop_duplicates(subset=['name']).sort_values('name')
    return {"cities": all_cities.to_dict(orient='records')}

def get_city_coords(df, city_name):
    # Lookup city coordinates from data
    for prefix in ['start', 'end']:
        match = df[df[f'{prefix}_location'] == city_name]
        if not match.empty:
            return match.iloc[0][f'{prefix}_lat'], match.iloc[0][f'{prefix}_lon']
    raise HTTPException(status_code=404, detail=f"City {city_name} not found")

@app.post("/optimize")
@app.post("/optimize-single")
def optimize_single(request: SingleOptimizationRequest):
    df = resources["df"]
    if df is None:
        raise HTTPException(status_code=500, detail="System not ready")

    start_lat, start_lon = get_city_coords(df, request.start_node)
    end_lat, end_lon = get_city_coords(df, request.end_node)

    # 1. Fetch Graph
    coords = [[start_lat, start_lon], [end_lat, end_lon]]
    G = get_dynamic_road_graph(coords)
    
    # 2. Apply Dynamic Conditions via Weight Engine
    G = apply_conditions(G, request.scenario)

    # 3. Find Route using Optimization Engine
    start_point = ox.distance.nearest_nodes(G, start_lon, start_lat)
    end_point = ox.distance.nearest_nodes(G, end_lon, end_lat)
    
    # Baseline Path (distance)
    base_coords, base_len, base_btime, _ = optimize_single_segment(G, start_point, end_point, weight='length')
    # AI Optimized Path
    ai_coords, ai_len, ai_btime, ai_time = optimize_single_segment(G, start_point, end_point, weight='ai_time_min')

    if not ai_coords:
        raise HTTPException(status_code=400, detail="No route found")

    # 4. Eco Engine (Fuel and CO2 calculation)
    base_fuel, base_co2 = calculate_emission(base_len, request.vehicle_type)
    ai_fuel, ai_co2 = calculate_emission(ai_len, request.vehicle_type)

    # Format Metrics to match existing UI
    time_saved = base_btime - ai_time
    cost_saved = base_fuel - ai_fuel
    time_efficiency = (time_saved / base_btime * 100) if base_btime > 0 else 0
    cost_efficiency = (cost_saved / base_fuel * 100) if base_fuel > 0 else 0
    
    alpha, beta, gamma = 1.0, 10.0, 0.5
    base_score = round((alpha * base_btime) + (beta * base_fuel) + (gamma * base_len), 2)
    ai_score = round((alpha * ai_time) + (beta * ai_fuel) + (gamma * ai_len), 2)

    return {
        "start_node": request.start_node,
        "end_node": request.end_node,
        "optimized_time": round(ai_time, 2),
        "baseline_time": round(base_btime, 2),
        "optimized_cost": round(ai_fuel, 2),
        "baseline_cost": round(base_fuel, 2),
        "time_saved": round(time_saved, 2),
        "cost_saved": round(cost_saved, 2),
        "time_efficiency": round(time_efficiency, 2),
        "cost_efficiency": round(cost_efficiency, 2),
        "baseline_score": base_score,
        "ai_score": ai_score,
        "opt_coords": ai_coords,
        "base_coords": base_coords,
        "co2_emission": round(ai_co2, 2)
    }

@app.post("/optimize-multi")
def optimize_multi(request: MultiOptimizationRequest):
    df = resources["df"]
    
    # Extract all coords
    all_cities = [request.origin] + request.stops + [request.destination]
    coords_list = [get_city_coords(df, city) for city in all_cities]

    G = get_dynamic_road_graph(coords_list)
    G = apply_conditions(G, request.scenario)
    
    nodes_list = [ox.distance.nearest_nodes(G, lon, lat) for lat, lon in coords_list]
    
    ai_coords, ai_len, _, ai_time = optimize_multi_stop_tsp(G, nodes_list, weight='ai_time_min')
    
    if not ai_coords:
        raise HTTPException(status_code=400, detail="Could not optimize multi-stop route")
        
    ai_fuel, ai_co2 = calculate_emission(ai_len, request.vehicle_type)
    
    return {
        "optimized_path_coords": ai_coords,
        "total_distance_km": round(ai_len, 2),
        "total_time_min": round(ai_time, 2),
        "fuel_used_liters": round(ai_fuel, 2),
        "co2_emission_kg": round(ai_co2, 2)
    }

@app.get("/report")
def get_report(start_node: str, end_node: str, opt_time: float, base_time: float, opt_cost: float, base_cost: float, time_eff: float, cost_eff: float, ai_score: float, base_score: float):
    """Generates and returns a PDF report."""
    markdown_content = f"""
# Logistics Route Optimization Report

## Executive Summary
Optimized delivery from **{start_node}** to **{end_node}**.

## Detailed Metrics

| Metric | Baseline Route | AI Optimized Route | Efficiency Gain |
| :--- | :--- | :--- | :--- |
| **Total Time** | {base_time} min | **{opt_time} min** | **+{round(time_eff, 2)}%** |
| **Fuel Cost** | ${base_cost} | **${opt_cost}** | **+{round(cost_eff, 2)}%** |
| **Route Quality Score** | {base_score} | **{ai_score}** | - |

> *Note: Route Quality Score is calculated as a weighted sum of Time, Fuel, and Distance, where lower is better.*

## Conclusion
The AI-Optimized route uses the real physical road network (via OSM) coupled with dynamic simulated traffic constraints to provide the most logically efficient path.
    """
    
    output_path = "reports/optimization_report.pdf"
    os.makedirs("reports", exist_ok=True)
    create_pdf_report(markdown_content, output_path)
    
    return FileResponse(output_path, media_type='application/pdf', filename="optimization_report.pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
