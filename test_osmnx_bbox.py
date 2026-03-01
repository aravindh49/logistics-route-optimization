import osmnx as ox
import time

print("Starting osmnx graph download from bbox...")
start = time.time()
try:
    # Bounding box for Tamil Nadu covering our 30 cities
    north, south, east, west = 13.5, 8.0, 80.5, 76.5
    
    # Custom filter to get major highways + connecting roads, skipping tiny residential streets
    custom_filter = '["highway"~"motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link"]'
    
    # graph_from_bbox is deprecated in recent osmnx, it recommends bbox argument in graph_from_polygon or using a bounding box tuple
    # Let's use the standard method for newer osmnx versions:
    # From OSMNX 2.0: ox.graph_from_bbox is removed. You create a bounding box polygon and pass it to graph_from_polygon
    G = ox.graph_from_bbox(bbox=(west, south, east, north), network_type="drive", custom_filter=custom_filter, simplify=True)
    ox.save_graphml(G, "data/tamil_nadu_bbox.graphml")
    print(f"Graph downloaded and saved in {time.time() - start} seconds.")
    print(f"Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")
except Exception as e:
    print(f"Fallback due to osmnx syntax: {e}")
    # Fallback syntax for newer versions if bbox function is missing or signature changed
    from shapely.geometry import box
    poly = box(west, south, east, north)
    # Using drive network type with custom filter
    G = ox.graph_from_polygon(poly, custom_filter=custom_filter, simplify=True)
    ox.save_graphml(G, "data/tamil_nadu_bbox.graphml")
    print(f"Graph from polygon downloaded and saved in {time.time() - start} seconds.")
    print(f"Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")
