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

def calculate_emission(distance_km, vehicle_type="diesel"):
    """
    Computes fuel used and CO2 emissions based on the vehicle profile.
    """
    v = VEHICLES.get(vehicle_type, VEHICLES["diesel"])
    fuel_used = distance_km * v["fuel_per_km"]
    co2 = fuel_used * v["co2_per_liter"]
    return fuel_used, co2
