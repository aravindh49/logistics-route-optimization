import networkx as nx
import osmnx as ox
from shapely.geometry import box
import random

def haversine_dist(lat1, lon1, lat2, lon2):
    import math
    R = 6371.0 # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_dynamic_road_graph(start_lat, start_lon, end_lat, end_lon):
    """Dynamically downloads bounding box road network with caching and dynamic buffer."""
    import time
    import os
    import hashlib
    
    os.makedirs("data/cached_graphs", exist_ok=True)
    
    # Create a unique key for this city pair (rounding to 3 decimals ~110m precision)
    pair_str = f"{round(start_lat,3)}_{round(start_lon,3)}_{round(end_lat,3)}_{round(end_lon,3)}"
    cache_key = hashlib.md5(pair_str.encode()).hexdigest()
    cache_path = f"data/cached_graphs/{cache_key}.graphml"

    if os.path.exists(cache_path):
        print(f"Loading cached dynamic graph from {cache_path}...")
        start = time.time()
        G = ox.load_graphml(cache_path)
        print(f"Loaded cached graph in {time.time() - start:.2f}s.")
        return G

    print("Dynamically fetching new road network for route...")
    start = time.time()
    
    # Upgrade 2: Smart Corridor Buffer based on distance
    dist = haversine_dist(start_lat, start_lon, end_lat, end_lon)
    if dist < 100:
        margin = 0.1  # ~11km
    elif dist < 300:
        margin = 0.2  # ~22km
    else:
        margin = 0.3  # ~33km

    north = max(start_lat, end_lat) + margin
    south = min(start_lat, end_lat) - margin
    # Ensure West is always < East! Fixed from previous code
    east = max(start_lon, end_lon) + margin
    west = min(start_lon, end_lon) - margin
    
    custom_filter = '["highway"~"motorway|trunk|primary|secondary|tertiary"]'
    G = ox.graph_from_bbox(bbox=(west, south, east, north), network_type="drive", custom_filter=custom_filter, simplify=True)
    
    # Pre-calculate speeds and times
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    
    # Upgrade 1: Graph Caching
    ox.save_graphml(G, cache_path)
    
    print(f"Downloaded and cached dynamic graph in {time.time() - start:.2f}s. Nodes: {len(G)}")
    return G

def optimize_real_route(G, start_lat, start_lon, end_lat, end_lon):
    """Runs OSMNX + A* to find both Baseline and AI optimized routes."""
    if G is None:
        try:
            G = get_dynamic_road_graph(start_lat, start_lon, end_lat, end_lon)
        except Exception as e:
            print(f"Dynamic graph fetching failed: {e}")
            return None
        
    start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
    end_node = ox.distance.nearest_nodes(G, end_lon, end_lat)
    
    # Define deterministic weight function based on real road logic!
    def calculate_edge_cost(edge_data):
        length_km = edge_data.get('length', 100) / 1000.0
        # Travel time is precalculated by ox.add_edge_travel_times in seconds, convert to mins
        base_time = edge_data.get('travel_time', length_km * 60) / 60.0 
        
        # Upgrade 3: Real Optimization Objective (Push traffic to highways)
        hw = edge_data.get('highway', '')
        # Simulated logic: local roads are congested, highways are clear
        if 'motorway' in hw or 'trunk' in hw:
            traffic_factor = 1.0 
        elif 'primary' in hw:
            traffic_factor = 1.2
        elif 'secondary' in hw:
            traffic_factor = 1.5
        else:
            traffic_factor = 2.0 # penalize local roads

        ai_time = base_time * traffic_factor
        fuel_cost = length_km * 0.15 # constant fuel per km for simplicity
        return length_km, base_time, ai_time, fuel_cost
        
    def dynamic_ai_weight(u, v, d):
        edge_data = G.get_edge_data(u, v)[0]
        _, _, ai_time, _ = calculate_edge_cost(edge_data)
        return ai_time
        
    def extract_path_details(G, path):
        coords = []
        total_len = 0
        total_base_time = 0
        total_ai_time = 0
        total_fuel = 0
        
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            # Nodes coordinates
            node_u = G.nodes[u]
            coords.append([node_u['y'], node_u['x']])
            
            # Edge data
            edge_data = G.get_edge_data(u, v)[0]
            length_km, base_time, ai_time, fuel_cost = calculate_edge_cost(edge_data)
            
            total_len += length_km
            total_base_time += base_time
            total_ai_time += ai_time
            total_fuel += fuel_cost
            
        # Append final node
        last_node = G.nodes[path[-1]]
        coords.append([last_node['y'], last_node['x']])
        
        return coords, total_len, total_base_time, total_ai_time, total_fuel

    # 1. Baseline Route: Pure shortest physical distance (naive A*)
    try:
        baseline_path = nx.astar_path(G, start_node, end_node, weight='length')
        base_coords, base_dist, base_time, _, base_fuel = extract_path_details(G, baseline_path)
    except nx.NetworkXNoPath:
        return None
        
    # 2. Optimized Route: Accounts for Traffic, Demand, and Time (AI A*)
    try:
        ai_path = nx.astar_path(G, start_node, end_node, weight=dynamic_ai_weight)
        ai_coords, ai_dist, _, ai_time, ai_fuel = extract_path_details(G, ai_path)
    except nx.NetworkXNoPath:
        ai_coords, ai_dist, ai_time, ai_fuel = base_coords, base_dist, base_time, base_fuel

    # Route Quality Score calculation
    # alpha * Time + beta * Fuel + gamma * Distance
    alpha, beta, gamma = 0.5, 0.3, 0.2
    
    # Baseline Quality Score
    base_score = (alpha * base_time) + (beta * base_fuel) + (gamma * base_dist)
    # AI Quality Score
    ai_score = (alpha * ai_time) + (beta * ai_fuel) + (gamma * ai_dist)

    results = {
        "baseline_coords": base_coords,
        "baseline_time": round(base_time, 2),
        "baseline_cost": round(base_fuel, 2),
        "baseline_score": round(base_score, 2),
        
        "ai_coords": ai_coords,
        "ai_time": round(ai_time, 2),
        "ai_cost": round(ai_fuel, 2),
        "ai_score": round(ai_score, 2),
    }
    
    return results
