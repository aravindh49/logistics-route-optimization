import osmnx as ox
import time

print("Starting osmnx graph download...")
start = time.time()
try:
    # Use custom filter to download only major highways (motorway, trunk, primary) for Logistics!
    # This prevents downloading tiny streets and makes state-level routing viable in seconds.
    custom_filter = '["highway"~"motorway|motorway_link|trunk|trunk_link|primary|primary_link"]'
    G = ox.graph_from_place("Tamil Nadu, India", custom_filter=custom_filter, simplify=True)
    ox.save_graphml(G, "data/tamil_nadu_highways.graphml")
    print(f"Highways Graph downloaded and saved in {time.time() - start} seconds.")
    print(f"Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")
except Exception as e:
    print(f"Error: {e}")
