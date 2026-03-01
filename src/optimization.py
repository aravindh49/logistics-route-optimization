import networkx as nx
import osmnx as ox
from shapely.geometry import box
import random

def optimize_real_route(G, start_lat, start_lon, end_lat, end_lon):
    """Runs OSMNX + A* to find both Baseline and AI optimized routes."""
    if G is None:
        print("Graph not available.")
        return None
        
    start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
    end_node = ox.distance.nearest_nodes(G, end_lon, end_lat)
    
    # Define dynamic weight functions for AI vs Baseline routing
    def dynamic_ai_weight(u, v, d):
        edge_data = G.get_edge_data(u, v)[0]
        length_km = edge_data.get('length', 100) / 1000.0
        # Travel time is precalculated by ox.add_edge_travel_times in seconds, convert to mins
        base_time = edge_data.get('travel_time', length_km * 60) / 60.0 
        
        # Simulate traffic dynamically for this path search (just use random seeded by edge id)
        # In a real app, this would query the ML model just like our previous system!
        traffic_factor = random.uniform(1.0, 2.5) 
        ai_time = base_time * traffic_factor
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
            length_km = edge_data.get('length', 0) / 1000.0
            base_time = edge_data.get('travel_time', length_km * 60) / 60.0
            
            traffic_factor = random.uniform(1.0, 2.5)
            ai_time = base_time * traffic_factor
            fuel_cost = length_km * random.uniform(0.12, 0.22) * traffic_factor
            
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
