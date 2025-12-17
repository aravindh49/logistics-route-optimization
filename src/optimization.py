import networkx as nx
import pandas as pd

def create_graph_from_data(df):
    """Creates a directed graph from the logistics data."""
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_edge(
            row['start_location'],
            row['end_location'],
            distance=row['distance_km'],
            demand=row['delivery_demand'],
            traffic=row['traffic_factor'],
            time_of_day=row['time_of_day']
        )
    return G

def find_optimized_route(graph, model, start_node, end_node, time_of_day='afternoon'):
    """
    Finds the optimized route using Dijkstra's algorithm with ML-predicted weights.

    Args:
        graph (nx.DiGraph): The graph of locations.
        model: The trained ML model for time prediction.
        start_node (str): The starting location.
        end_node (str): The destination location.
        time_of_day (str): The time of day for the prediction.

    Returns:
        tuple: A tuple containing the path (list of nodes) and total predicted time.
    """
    # Use the ML model to predict travel time (edge weight)
    def weight_func(u, v, d):
        edge_data = graph.get_edge_data(u, v)
        # Create a DataFrame for prediction
        feature_df = pd.DataFrame([{
            'distance_km': edge_data['distance'],
            'delivery_demand': edge_data['demand'],
            'traffic_factor': edge_data['traffic'],
            'time_of_day': time_of_day
        }])
        # Predict time
        predicted_time = model.predict(feature_df)[0]
        return predicted_time

    try:
        # Find the shortest path using Dijkstra's algorithm with the ML model's prediction as weight
        path = nx.dijkstra_path(graph, source=start_node, target=end_node, weight=weight_func)
        total_time = nx.dijkstra_path_length(graph, source=start_node, target=end_node, weight=weight_func)
        return path, total_time
    except nx.NetworkXNoPath:
        return None, None

def find_baseline_route(graph, start_node, end_node):
    """Finds the shortest path based on distance only (baseline)."""
    try:
        path = nx.dijkstra_path(graph, source=start_node, target=end_node, weight='distance')
        
        # Calculate total time for this path based on simple estimation
        total_time = 0
        for i in range(len(path) - 1):
            edge_data = graph.get_edge_data(path[i], path[i+1])
            total_time += (edge_data['distance'] / 60) * 60 * edge_data['traffic']
        return path, total_time
    except nx.NetworkXNoPath:
        return None, None

def calculate_path_cost(graph, path):
    """Calculates the total fuel cost for a given path."""
    total_cost = 0
    if not path or len(path) < 2:
        return 0
    
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        edge_data = graph.get_edge_data(u, v)
        if edge_data:
            # Default fuel cost to 0.2 if not present (though our generator adds it)
            fuel_cost_per_km = edge_data.get('fuel_cost_per_km', 0.2)
            distance = edge_data.get('distance', 0)
            total_cost += distance * fuel_cost_per_km
            
    return total_cost
