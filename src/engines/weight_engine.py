import random

def apply_conditions(G, settings):
    """
    Applies live conditions to the graph G directly modifying edge data to apply weight.
    Returns the modified Graph.
    """
    # Create or use provided graph
    for u, v, data in G.edges(data=True):
        length_km = data.get('length', 100) / 1000.0
        base_time = data.get('travel_time', length_km * 60) / 60.0 # mins
        
        # Base factor based on road type
        hw = data.get('highway', '')
        if 'motorway' in hw or 'trunk' in hw:
            traffic_factor = 1.0 
        elif 'primary' in hw:
            traffic_factor = 1.2
        elif 'secondary' in hw:
            traffic_factor = 1.5
        else:
            traffic_factor = 2.0
            
        # Live Condition Simulator
        if getattr(settings, 'heavy_rain', False):
            traffic_factor *= 1.2
            
        if getattr(settings, 'rush_hour', False) and hw in ["primary", "secondary"]:
            traffic_factor *= 1.4
            
        if getattr(settings, 'accident_zone', False):
            # Deterministic mock rule for accident zone based on edge ID or just a fixed random seed
            if random.random() < 0.05: 
                traffic_factor *= 5.0
                
        ai_time = base_time * traffic_factor
        
        # We store details in edge data
        data["ai_time_min"] = ai_time
        data["base_time_min"] = base_time
        data["length_km"] = length_km
        
        # Note: Fuel cost now tracked cleanly here initially or handled dynamically 
        # but since Eco Engine uses full path distance, we will handle fuel/co2 via Eco Engine
        # based on path distance.
    return G
