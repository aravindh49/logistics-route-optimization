import pandas as pd
import numpy as np
from faker import Faker
import os
import math

# List of 30 Major US Cities with Coordinates
CITIES = [
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
    {"name": "Houston", "lat": 29.7604, "lon": -95.3698},
    {"name": "Phoenix", "lat": 33.4484, "lon": -112.0740},
    {"name": "Philadelphia", "lat": 39.9526, "lon": -75.1652},
    {"name": "San Antonio", "lat": 29.4241, "lon": -98.4936},
    {"name": "San Diego", "lat": 32.7157, "lon": -117.1611},
    {"name": "Dallas", "lat": 32.7767, "lon": -96.7970},
    {"name": "San Jose", "lat": 37.3382, "lon": -121.8863},
    {"name": "Austin", "lat": 30.2672, "lon": -97.7431},
    {"name": "Jacksonville", "lat": 30.3322, "lon": -81.6557},
    {"name": "Fort Worth", "lat": 32.7555, "lon": -97.3308},
    {"name": "Columbus", "lat": 39.9612, "lon": -82.9988},
    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194},
    {"name": "Charlotte", "lat": 35.2271, "lon": -80.8431},
    {"name": "Indianapolis", "lat": 39.7684, "lon": -86.1581},
    {"name": "Seattle", "lat": 47.6062, "lon": -122.3321},
    {"name": "Denver", "lat": 39.7392, "lon": -104.9903},
    {"name": "Washington DC", "lat": 38.9072, "lon": -77.0369},
    {"name": "Boston", "lat": 42.3601, "lon": -71.0589},
    {"name": "El Paso", "lat": 31.7619, "lon": -106.4850},
    {"name": "Nashville", "lat": 36.1627, "lon": -86.7816},
    {"name": "Detroit", "lat": 42.3314, "lon": -83.0458},
    {"name": "Oklahoma City", "lat": 35.4676, "lon": -97.5164},
    {"name": "Portland", "lat": 45.5152, "lon": -122.6784},
    {"name": "Las Vegas", "lat": 36.1699, "lon": -115.1398},
    {"name": "Memphis", "lat": 35.1495, "lon": -90.0490},
    {"name": "Louisville", "lat": 38.2527, "lon": -85.7585},
    {"name": "Baltimore", "lat": 39.2904, "lon": -76.6122}
]

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    R = 6371  # Radius of earth in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c
    return d

def generate_logistics_data(num_records=500, num_cities=30, data_path="data/logistics_data.csv"):
    """
    Generates a synthetic logistics dataset using REAL locations and saves it to a CSV file.
    """
    # Use the defined list of real cities
    cities = CITIES[:num_cities]
    
    data = []
    
    # Ensure full connectivity (mesh) or random? 
    # Let's generate random routes from this set
    for _ in range(num_records):
        start = np.random.choice(cities)
        end = np.random.choice(cities)
        
        while start['name'] == end['name']:
            end = np.random.choice(cities)
            
        dist = haversine_distance(start['lat'], start['lon'], end['lat'], end['lon'])
        
        # Add noise to distance to simulate road winding? 
        # For simplicity, we keep it as "flight distance" or multiply by a factor (e.g. 1.2x)
        road_distance = dist * 1.2
        
        record = {
            "start_location": start['name'],
            "start_lat": start['lat'],
            "start_lon": start['lon'],
            "end_location": end['name'],
            "end_lat": end['lat'],
            "end_lon": end['lon'],
            "distance_km": road_distance,
            "delivery_demand": np.random.randint(10, 100),
            "fuel_cost_per_km": np.random.uniform(0.1, 0.3),
            "traffic_factor": np.random.uniform(1.0, 2.5),
            "time_of_day": np.random.choice(['morning', 'afternoon', 'evening', 'night'])
        }
        data.append(record)

    df = pd.DataFrame(data)

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    
    df.to_csv(data_path, index=False)
    print(f"Generated {num_records} real-world records and saved to {data_path}")

if __name__ == '__main__':
    generate_logistics_data(num_records=500)
