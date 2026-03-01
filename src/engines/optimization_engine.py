import networkx as nx

def extract_path_metrics(G, path):
    coords = []
    total_len = 0
    total_base_time = 0
    total_ai_time = 0
    
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        node_u = G.nodes[u]
        coords.append([node_u['y'], node_u['x']])
        
        edge_data = G.get_edge_data(u, v)[0]
        total_len += edge_data.get('length_km', 0)
        total_base_time += edge_data.get('base_time_min', 0)
        total_ai_time += edge_data.get('ai_time_min', 0)
        
    last_node = G.nodes[path[-1]]
    coords.append([last_node['y'], last_node['x']])
    
    return coords, total_len, total_base_time, total_ai_time

def optimize_single_segment(G, start_node, end_node, weight='ai_time_min'):
    try:
        path = nx.astar_path(G, start_node, end_node, weight=weight)
        return extract_path_metrics(G, path)
    except nx.NetworkXNoPath:
        return [], 0, 0, 0

def optimize_multi_stop_tsp(G, nodes_list, weight='ai_time_min'):
    """
    Uses OR-Tools to solve TSP over the nodes_list correctly ordered.
    nodes_list: [start, stop1, stop2, ..., end]
    Since OR-Tools TSP naturally forms a cycle, to find a path from exact start to exact end,
    we can use the exact parameters manager.
    nodes_list[0] = Origin
    nodes_list[-1] = Destination
    """
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    
    n = len(nodes_list)
    dist_matrix = [[0]*n for _ in range(n)]
    path_matrix = [[None]*n for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            if i != j:
                try:
                    p = nx.astar_path(G, nodes_list[i], nodes_list[j], weight=weight)
                    path_matrix[i][j] = p
                    cost = sum([G.get_edge_data(p[k], p[k+1])[0].get(weight, 0) for k in range(len(p)-1)])
                    dist_matrix[i][j] = int(cost * 100) # scale to int for ORTools
                except nx.NetworkXNoPath:
                    dist_matrix[i][j] = 999999999
    
    # 2. Setup OR-Tools Routing Model
    manager = pywrapcp.RoutingIndexManager(n, 1, [0], [n-1]) # Fixed start and end idx
    routing = pywrapcp.RoutingModel(manager)
    
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return dist_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Solve
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    
    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        return None, None
        
    index = routing.Start(0)
    ordered_ids = []
    while not routing.IsEnd(index):
        node_index = manager.IndexToNode(index)
        ordered_ids.append(node_index)
        index = solution.Value(routing.NextVar(index))
    ordered_ids.append(manager.IndexToNode(index))
    
    # Reconstruct final route by combining paths
    full_coords = []
    full_len = 0
    full_base_time = 0
    full_ai_time = 0
    
    for i in range(len(ordered_ids) - 1):
        u_idx = ordered_ids[i]
        v_idx = ordered_ids[i+1]
        path = path_matrix[u_idx][v_idx]
        
        # Avoid duplicating the overlapping intersection node for each sub-path
        coords, l, btime, atime = extract_path_metrics(G, path)
        if i == len(ordered_ids) - 2:
            full_coords.extend(coords)
        else:
            full_coords.extend(coords[:-1])
            
        full_len += l
        full_base_time += btime
        full_ai_time += atime
        
    return full_coords, full_len, full_base_time, full_ai_time
