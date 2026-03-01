import osmnx as ox
import traceback

print("Downloading TN graph...")
try:
    # Use graph_from_bbox directly to avoid geometry intersection slowness
    # Tamil Nadu BBOX
    west, south, east, north = 76.2, 8.0, 80.4, 13.6
    
    # Restrict to only the most major highways to stay within memory limits for such a large area
    G = ox.graph_from_bbox(
        bbox=(west, south, east, north),
        network_type='drive',
        custom_filter='["highway"~"motorway|trunk|primary"]',
        simplify=True
    )
    
    # Precompute speeds and times for faster routing
    print("Graph downloaded, processing speeds...")
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    
    ox.save_graphml(G, 'data/tn_highways.graphml')
    print(f"Done downloading graph! Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")
except Exception as e:
    print(f"Failed: {e}")
    traceback.print_exc()
