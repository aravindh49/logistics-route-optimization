import osmnx as ox
import time
import os
import hashlib
import math

def haversine_dist(lat1, lon1, lat2, lon2):
    R = 6371.0 # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_dynamic_road_graph(coords: list, global_graph=None):
    """
    Dynamically downloads bounding box road network with caching and dynamic buffer.
    coords is a list of [lat, lon] lists representing all nodes to visit.
    """
    os.makedirs("data/cached_graphs", exist_ok=True)
    
    lats = [c[0] for c in coords]
    lons = [c[1] for c in coords]
    
    # Create precise cache key so any matching coord list hits cache
    pair_str = "_".join([f"{round(lat, 3)}_{round(lon, 3)}" for lat, lon in coords])
    cache_key = hashlib.md5(pair_str.encode()).hexdigest()
    cache_path = f"data/cached_graphs/{cache_key}.graphml"

    if os.path.exists(cache_path):
        print(f"Loading cached dynamic graph from {cache_path}...")
        start = time.time()
        G = ox.load_graphml(cache_path)
        print(f"Loaded cached graph in {time.time() - start:.2f}s. Nodes: {len(G)}")
        return G

    print("Dynamically fetching new road network for route corridor...")
    start = time.time()
    
    # Calculate max distance across consecutive segments to determine buffer
    max_dist = 0
    if len(lats) > 1:
        max_dist = max([haversine_dist(lats[i], lons[i], lats[i+1], lons[i+1]) for i in range(len(lats)-1)])
    
    if max_dist < 100:
        margin = 0.1
        custom_filter = '["highway"~"motorway|trunk|primary|secondary|tertiary"]'
    elif max_dist < 300:
        margin = 0.2
        custom_filter = '["highway"~"motorway|trunk|primary|secondary"]'
    else:
        margin = 0.3
        custom_filter = '["highway"~"motorway|trunk|primary"]'

    north = max(lats) + margin
    south = min(lats) - margin
    common = min(lons) - margin
    east = max(lons) + margin
    west = common

    if global_graph is not None:
        print("Extracting corridor subgraph from global pre-loaded map...")
        start_truncate = time.time()
        G_sub = ox.truncate.truncate_graph_bbox(global_graph, bbox=(west, south, east, north))
        # Important: MUST copy the subgraph so weight engine modifiers don't pollute global graph
        G_sub = G_sub.copy()
        print(f"Extracted subgraph in {time.time() - start_truncate:.2f}s. Nodes: {len(G_sub)}")
        # In case it's completely empty...
        if len(G_sub) > 0:
            return G_sub
        else:
            print("Subgraph extraction yielded empty graph. Falling back to Overpass download...")

    print("Dynamically fetching new road network from Overpass...")
    G = ox.graph_from_bbox(bbox=(west, south, east, north), network_type="drive", custom_filter=custom_filter, simplify=True)
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    
    ox.save_graphml(G, cache_path)
    
    print(f"Downloaded dynamic graph in {time.time() - start:.2f}s. Nodes: {len(G)}")
    return G
