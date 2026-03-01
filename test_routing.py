import osmnx as ox
import time
import networkx as nx

start_city = (8.7139, 77.7567) # Tirunelveli
end_city = (8.7642, 78.1348) # Thoothukudi

# Bbox around the two cities with 0.1 degree margin (~10km)
north = max(start_city[0], end_city[0]) + 0.1
south = min(start_city[0], end_city[0]) - 0.1
east = max(start_city[1], end_city[1]) + 0.1
west = min(start_city[1], end_city[1]) - 0.1

print(f"Downloading from bbox: {north}, {south}, {east}, {west}")

# Major roads only to keep it incredibly fast
custom_filter = '["highway"~"motorway|trunk|primary|secondary|tertiary"]'

start = time.time()
try:
    G = ox.graph_from_bbox(bbox=(west, south, east, north), network_type="drive", custom_filter=custom_filter, simplify=True)
    print(f"Graph loaded in {time.time() - start} seconds. Nodes: {len(G)}")
    
    # Snap to nodes
    start_node = ox.distance.nearest_nodes(G, start_city[1], start_city[0])
    end_node = ox.distance.nearest_nodes(G, end_city[1], end_city[0])
    
    # Route
    route = nx.astar_path(G, start_node, end_node, weight='length')
    print(f"Route found with {len(route)} nodes.")
except Exception as e:
    print(f"Bbox failed: {e}")
    from shapely.geometry import box
    poly = box(west, south, east, north)
    start = time.time()
    G = ox.graph_from_polygon(poly, custom_filter=custom_filter, simplify=True)
    print(f"Graph loaded in {time.time() - start} seconds. Nodes: {len(G)}")
    
    # Snap to nodes
    start_node = ox.distance.nearest_nodes(G, start_city[1], start_city[0])
    end_node = ox.distance.nearest_nodes(G, end_city[1], end_city[0])
    
    # Route
    route = nx.astar_path(G, start_node, end_node, weight='length')
    print(f"Route found with {len(route)} nodes.")

