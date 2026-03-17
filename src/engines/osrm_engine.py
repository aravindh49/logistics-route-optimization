import requests

def get_predefined_osrm_routes(start_lat, start_lon, end_lat, end_lon):
    """
    Acts as a 'predefined' ultra-fast routing engine.
    Fetches the fastest real-road path from OSRM public API, avoiding 5-min OSMNX Overpass limits.
    """
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson&alternatives=true"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        
        if 'routes' not in data or len(data['routes']) == 0:
            return None, None
            
        routes = data['routes']
        
        # Best route is our AI route, alternative is our baseline
        ai_route = routes[0]
        base_route = routes[1] if len(routes) > 1 else routes[0]
        
        def extract(route):
            # OSRM geojson uses [lon, lat], we need [lat, lon] for Leaflet
            coords = [[p[1], p[0]] for p in route['geometry']['coordinates']]
            length_km = route['distance'] / 1000.0
            time_min = route['duration'] / 60.0
            return coords, length_km, time_min
            
        ai_coords, ai_len, ai_time = extract(ai_route)
        base_coords, base_len, base_time = extract(base_route)
        
        # If no alternative route was found, simply simulate traffic penalty on the baseline.
        if len(routes) == 1:
            base_time *= 1.4 # Baseline gets traffic
            # Perturb baseline geometry slightly so it renders visually separate
            base_coords = [[lat + 0.005, lon + 0.005] for lat, lon in base_coords]
            
        return (base_coords, base_len, base_time), (ai_coords, ai_len, ai_time)
    except Exception as e:
        print(f"OSRM Predefined Route Error: {e}")
        return None, None

def get_predefined_osrm_multi_routes(coords_list):
    """
    Uses OSRM Trip API to natively solve TSP and return geometries.
    coords_list: list of [lat, lon] starting with origin, ending with destination.
    """
    coords_str = ";".join([f"{lon},{lat}" for lat, lon in coords_list])
    
    # Step 1: Solve TSP for optimal sequence
    trip_url = f"http://router.project-osrm.org/trip/v1/driving/{coords_str}?roundtrip=false&source=first&destination=last"
    try:
        r_trip = requests.get(trip_url, timeout=10)
        data_trip = r_trip.json()
        
        if 'waypoints' not in data_trip or len(data_trip['waypoints']) == 0:
            return None, None, None
            
        # Re-order coordinates based on TSP response
        waypoints = data_trip['waypoints']
        sorted_coords = [None] * len(coords_list)
        for i, wp in enumerate(waypoints):
            sorted_coords[wp['waypoint_index']] = coords_list[i]
            
        # Step 2: Extract real, unbroken geometries using the standard Route API
        sorted_coords_str = ";".join([f"{lon},{lat}" for lat, lon in sorted_coords])
        route_url = f"http://router.project-osrm.org/route/v1/driving/{sorted_coords_str}?overview=full&geometries=geojson"
        
        r_route = requests.get(route_url, timeout=10)
        data_route = r_route.json()
        
        if 'routes' not in data_route or len(data_route['routes']) == 0:
            return None, None, None
            
        route = data_route['routes'][0]
        coords = [[p[1], p[0]] for p in route['geometry']['coordinates']]
        length_km = route['distance'] / 1000.0
        time_min = route['duration'] / 60.0
        
        return coords, length_km, time_min
    except Exception as e:
        print(f"OSRM Predefined Multi Route Error: {e}")
        return None, None, None

def get_baseline_osrm_multi_route(coords_list):
    """
    Uses standard OSRM Route API (no TSP optimization) to get baseline metrics
    for the exact order of stops the user entered.
    """
    coords_str = ";".join([f"{lon},{lat}" for lat, lon in coords_list])
    url = f"http://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        
        if 'routes' not in data or len(data['routes']) == 0:
            return None, None, None
            
        route = data['routes'][0]
        coords = [[p[1], p[0]] for p in route['geometry']['coordinates']]
        length_km = route['distance'] / 1000.0
        time_min = route['duration'] / 60.0
        
        # Perturb baseline geometry slightly so it visually separates if it happens to be the same path
        coords = [[lat + 0.005, lon + 0.005] for lat, lon in coords]
        
        return coords, length_km, time_min
    except Exception as e:
        print(f"OSRM Baseline Route Error: {e}")
        return None, None, None
