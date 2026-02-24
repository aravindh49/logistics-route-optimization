from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import joblib
import os

from src.optimization import create_graph_from_data, find_optimized_route, find_baseline_route, calculate_path_cost
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
    "model": None,
    "graph": None
}

def load_resources():
    """Loads CSV data, Model, and Graph into memory on startup."""
    try:
        print("Creating Resources...")
        resources["df"] = pd.read_csv("data/logistics_data.csv")
        resources["model"] = joblib.load("models/delivery_time_predictor.pkl")
        resources["graph"] = create_graph_from_data(resources["df"])
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
    
    # Extract Start and End cities to ensure we get all unique locations
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
    """Calculates the best route vs baseline."""
    graph = resources["graph"]
    model = resources["model"]
    start = request.start_node
    end = request.end_node

    if not graph or not model:
        raise HTTPException(status_code=500, detail="System not ready")

    if start not in graph.nodes or end not in graph.nodes:
        raise HTTPException(status_code=404, detail="City not found in network")

    # 1. Calculate Optimized Route (AI)
    opt_path, opt_time = find_optimized_route(graph, model, start, end)
    
    # 2. Calculate Baseline Route (Distance)
    base_path, base_time = find_baseline_route(graph, start, end)

    if not opt_path:
        raise HTTPException(status_code=400, detail="No route found")

    # 3. Cost Calculations
    opt_cost = calculate_path_cost(graph, opt_path)
    base_cost = calculate_path_cost(graph, base_path)

    # 4. Metrics
    time_saved = base_time - opt_time
    cost_saved = base_cost - opt_cost
    efficiency = (time_saved / base_time * 100) if base_time > 0 else 0

    # 5. Coordinates for Mapping
    df = resources["df"]
    # Quick lookup map
    city_map = {}
    for _, row in df.iterrows():
        city_map[row['start_location']] = [row['start_lat'], row['start_lon']]
        city_map[row['end_location']] = [row['end_lat'], row['end_lon']]

    return {
        "start_node": start,
        "end_node": end,
        "optimized_time": round(opt_time, 2),
        "baseline_time": round(base_time, 2),
        "optimized_cost": round(opt_cost, 2),
        "baseline_cost": round(base_cost, 2),
        "time_saved": round(time_saved, 2),
        "cost_saved": round(cost_saved, 2),
        "efficiency_gain": round(efficiency, 2),
        "opt_coords": [city_map.get(c) for c in opt_path],
        "base_coords": [city_map.get(c) for c in base_path]
    }

@app.get("/report")
def get_report(start_node: str, end_node: str, opt_time: float, base_time: float):
    """Generates and returns a PDF report."""
    time_saved = float(base_time) - float(opt_time)
    efficiency = (time_saved / float(base_time) * 100) if float(base_time) > 0 else 0
    
    markdown_content = f"""
# Logistics Route Optimization Report

## Executive Summary
Optimized delivery from **{start_node}** to **{end_node}**.

## Results

| Metric | Baseline | AI Optimized | Improvement |
| :--- | :--- | :--- | :--- |
| **Total Time** | {base_time} min | **{opt_time} min** | **{round(time_saved, 2)} min** |
| **Efficiency** | - | - | **{round(efficiency, 2)}%** |

## Conclusion
The AI-Optimized route provides a significantly faster delivery path.
    """
    
    output_path = "reports/optimization_report.pdf"
    os.makedirs("reports", exist_ok=True)
    create_pdf_report(markdown_content, output_path)
    
    return FileResponse(output_path, media_type='application/pdf', filename="optimization_report.pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
