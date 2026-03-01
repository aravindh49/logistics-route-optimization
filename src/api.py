from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import joblib
import os

from src.optimization import optimize_real_route
from src.generate_pdf_report import create_pdf_report

# --- Application Setup ---
app = FastAPI(title="Logistics Optimization API | TamilNaduAI")

# Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Static Files (CSS/JS)
app.mount("/static", StaticFiles(directory="web"), name="static")

# --- Global Resources ---
resources = {
    "df": None,
    "tn_graph": None
}

def load_resources():
    """Loads CSV data and OSMNX Graph into memory on startup."""
    try:
        print("Creating Resources...")
        resources["df"] = pd.read_csv("data/logistics_data.csv")
        
        graph_path = "data/tn_highways.graphml"
        if os.path.exists(graph_path):
            print(f"Loading GraphML from {graph_path}...")
            import osmnx as ox
            resources["tn_graph"] = ox.load_graphml(graph_path)
            print(f"✅ Loaded GraphML with {len(resources['tn_graph'])} nodes.")
        else:
            print("⚠️ tn_highways.graphml not found! Run download script first.")

        print("✅ Resources Loaded Successfully.")
    except Exception as e:
        print(f"❌ Error loading resources: {e}")

# Load immediately
load_resources()

# --- Data Models ---
class OptimizationRequest(BaseModel):
    start_node: str
    end_node: str

# --- Endpoints ---

@app.get("/")
async def read_index():
    return FileResponse('web/index.html')

@app.get("/cities")
def get_cities():
    """Returns a list of unique cities with coordinates for the dropdowns."""
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

@app.post("/optimize")
def optimize_route(request: OptimizationRequest):
    """Calculates the best route vs baseline using Real Road Network (OSMNX)."""
    df = resources["df"]
    start = request.start_node
    end = request.end_node

    if df is None:
        raise HTTPException(status_code=500, detail="System not ready")

    # Get coordinates
    start_data = df[df['start_location'] == start].iloc[0] if not df[df['start_location'] == start].empty else None
    end_data = df[df['end_location'] == end].iloc[0] if not df[df['end_location'] == end].empty else None

    if start_data is None or end_data is None:
        raise HTTPException(status_code=404, detail="City not found in network")
        
    start_lat, start_lon = start_data['start_lat'], start_data['start_lon']
    end_lat, end_lon = end_data['end_lat'], end_data['end_lon']

    # 1. Calculate Routes via OSMNX Real Map
    sim_results = optimize_real_route(resources["tn_graph"], start_lat, start_lon, end_lat, end_lon)

    if not sim_results:
        raise HTTPException(status_code=400, detail="No route found between coordinates")

    # Metrics
    opt_time = sim_results['ai_time']
    base_time = sim_results['baseline_time']
    opt_cost = sim_results['ai_cost']
    base_cost = sim_results['baseline_cost']
    
    # 2. Guarantee optimization: if AI predicts a worse time, fallback to baseline
    if opt_time > base_time:
        opt_time = base_time
        opt_cost = base_cost
        sim_results['ai_coords'] = sim_results['baseline_coords']

    # 3. Efficiency calculations requested by user
    time_saved = base_time - opt_time
    cost_saved = base_cost - opt_cost
    
    time_efficiency = (time_saved / base_time * 100) if base_time > 0 else 0
    cost_efficiency = (cost_saved / base_cost * 100) if base_cost > 0 else 0

    return {
        "start_node": start,
        "end_node": end,
        "optimized_time": round(opt_time, 2),
        "baseline_time": round(base_time, 2),
        "optimized_cost": round(opt_cost, 2),
        "baseline_cost": round(base_cost, 2),
        "time_saved": round(time_saved, 2),
        "cost_saved": round(cost_saved, 2),
        "time_efficiency": round(time_efficiency, 2),
        "cost_efficiency": round(cost_efficiency, 2),
        "baseline_score": sim_results['baseline_score'],
        "ai_score": sim_results['ai_score'],
        "opt_coords": sim_results['ai_coords'],
        "base_coords": sim_results['baseline_coords']
    }

@app.get("/report")
def get_report(start_node: str, end_node: str, opt_time: float, base_time: float, opt_cost: float, base_cost: float, time_eff: float, cost_eff: float, ai_score: float, base_score: float):
    """Generates and returns a PDF report."""
    time_saved = float(base_time) - float(opt_time)
    
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
