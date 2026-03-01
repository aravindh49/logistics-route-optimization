import osmnx as ox
import time

print("Starting osmnx graph download...")
start = time.time()
try:
    # Use simplify=True, retain_all=False to get a cleaner graph
    G = ox.graph_from_place("Tamil Nadu, India", network_type="drive", simplify=True)
    ox.save_graphml(G, "data/tamil_nadu_drive.graphml")
    print(f"Graph downloaded and saved in {time.time() - start} seconds.")
    print(f"Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")
except Exception as e:
    print(f"Error: {e}")
