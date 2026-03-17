VEHICLES = {
    "diesel": {
        "fuel_per_km": 0.25,
        "co2_per_liter": 2.68
    },
    "electric": {
        "fuel_per_km": 0.0,
        "co2_per_liter": 0.82  # grid-based equivalence
    }
}

def calculate_emission(distance_km, time_min=None, vehicle_type="diesel"):
    """
    Computes fuel used and CO2 emissions based on the vehicle profile and time spent in traffic.
    """
    v = VEHICLES.get(vehicle_type, VEHICLES["diesel"])
    
    if time_min is None:
        time_min = distance_km # Fallback if time not provided
        
    # Traffic penalty: idling and slow driving burns extra fuel
    # Assume base speed is 1km/min (60km/h). Extra time = traffic!
    extra_time_in_traffic = max(0, time_min - distance_km)
    
    # 0.05 liters per extra minute spent in traffic
    traffic_fuel_penalty = extra_time_in_traffic * 0.05
    
    fuel_used = (distance_km * v["fuel_per_km"]) + traffic_fuel_penalty
    co2 = fuel_used * v["co2_per_liter"]
    return fuel_used, co2
