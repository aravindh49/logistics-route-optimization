from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import joblib
import networkx as nx
import base64
import io
import os

from src.optimization import create_graph_from_data, find_optimized_route, find_baseline_route, calculate_path_cost
from src.visualization import visualize_routes
from src.generate_pdf_report import create_pdf_report

app = FastAPI(title="Logistics Optimization API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Static Files
app.mount("/static", StaticFiles(directory="web"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('web/index.html')

# Global variables
df = None
model = None
graph = None
preprocessor = None

def load_resources():
    global df, model, graph, preprocessor
    try:
        print("Loading resources...")
        df = pd.read_csv("data/logistics_data.csv")
        # Load the pipeline (which contains both preprocessor and regressor)
        model = joblib.load("models/delivery_time_predictor.pkl")
        
        # Precompute graph
        graph = create_graph_from_data(df)
        print("Resources loaded successfully.")
    except Exception as e:
        print(f"Error loading resources: {e}")

# Load on startup
load_resources()

class OptimizationRequest(BaseModel):
    start_node: str
    end_node: str

@app.get("/cities")
def get_cities():
    if df is None:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    # Extract unique cities with coordinates
    start_cities = df[['start_location', 'start_lat', 'start_lon']].rename(
        columns={'start_location': 'name', 'start_lat': 'lat', 'start_lon': 'lon'}
    )
    end_cities = df[['end_location', 'end_lat', 'end_lon']].rename(
        columns={'end_location': 'name', 'end_lat': 'lat', 'end_lon': 'lon'}
    )
    
    all_cities = pd.concat([start_cities, end_cities]).drop_duplicates(subset=['name']).sort_values('name')
    return {"cities": all_cities.to_dict(orient='records')}

def get_coords(city_name):
    # Helper to get coords for a city
    if df is None: return None
    row = df[df['start_location'] == city_name].iloc[0]
    return [row['start_lat'], row['start_lon']]
    
@app.post("/optimize")
def optimize_route(request: OptimizationRequest):
    if graph is None or model is None:
        raise HTTPException(status_code=500, detail="System not ready")

    start_node = request.start_node
    end_node = request.end_node

    if start_node not in graph.nodes or end_node not in graph.nodes:
        raise HTTPException(status_code=404, detail="City not found in network")

    # 1. Calculate Routes
    optimized_path, optimized_time = find_optimized_route(graph, model, start_node, end_node)
    baseline_path, baseline_time = find_baseline_route(graph, start_node, end_node)

    if not optimized_path:
        raise HTTPException(status_code=400, detail="No path found between selected cities")

    # 2. Calculate Costs
    optimized_cost = calculate_path_cost(graph, optimized_path)
    baseline_cost = calculate_path_cost(graph, baseline_path)

    # 3. Calculate Metrics
    time_saved = baseline_time - optimized_time
    cost_saved = baseline_cost - optimized_cost
    efficiency_gain = (time_saved / baseline_time * 100) if baseline_time > 0 else 0

    # 4. Get Coordinates for paths
    city_lookup = {}
    for _, row in df.iterrows():
        city_lookup[row['start_location']] = [row['start_lat'], row['start_lon']]
        city_lookup[row['end_location']] = [row['end_lat'], row['end_lon']]

    opt_coords = [city_lookup.get(city) for city in optimized_path]
    base_coords = [city_lookup.get(city) for city in baseline_path]

    return {
        "start_node": start_node,
        "end_node": end_node,
        "optimized_time": round(optimized_time, 2),
        "baseline_time": round(baseline_time, 2),
        "optimized_cost": round(optimized_cost, 2),
        "baseline_cost": round(baseline_cost, 2),
        "time_saved": round(time_saved, 2),
        "cost_saved": round(cost_saved, 2),
        "efficiency_gain": round(efficiency_gain, 2),
        "optimized_path": optimized_path,
        "baseline_path": baseline_path,
        "opt_coords": opt_coords,
        "base_coords": base_coords
    }

@app.get("/report")
def get_report(start_node: str, end_node: str, opt_time: float, base_time: float):
    # This is a dynamic report generator. 
    time_saved = float(base_time) - float(opt_time)
    efficiency = (time_saved / float(base_time) * 100) if float(base_time) > 0 else 0
    
    markdown_content = f"""
# Logistics Route Optimization Report

## Executive Summary
This report compares the baseline routing strategy against our AI-Optimized routing model for the delivery from **{start_node}** to **{end_node}**.

## Results Analysis

| Metric | Baseline (Distance-Based) | Optimized (AI-Driven) | Improvement |
| :--- | :--- | :--- | :--- |
| **Total Time** | {base_time} min | **{opt_time} min** | **{round(time_saved, 2)} min** |
| **Efficiency** | - | - | **{round(efficiency, 2)}%** |

## Methodology
- **Baseline**: calculated using standard Dijkstra algorithm minimizing Euclidean distance.
- **Optimized**: calculated using Random Forest Regression to predict travel time based on traffic, demand, and time of day.

## Conclusion
The AI-Optimized route provides a significantly faster delivery path by avoiding predicted high-traffic segments.
    """
    
    output_path = "reports/user_generated_report.pdf"
    create_pdf_report(markdown_content, output_path)
    
    return FileResponse(output_path, media_type='application/pdf', filename="optimization_report.pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
