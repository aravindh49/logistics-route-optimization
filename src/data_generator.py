import pandas as pd
import numpy as np
from faker import Faker
import os
import math

# List of 30 Major US Cities with Coordinates
# List of Major Cities in Tamil Nadu, India
CITIES = [
    {"name": "Chennai", "lat": 13.0827, "lon": 80.2707},
    {"name": "Coimbatore", "lat": 11.0168, "lon": 76.9558},
    {"name": "Madurai", "lat": 9.9252, "lon": 78.1198},
    {"name": "Tiruchirappalli", "lat": 10.7905, "lon": 78.7047},
    {"name": "Salem", "lat": 11.6643, "lon": 78.1460},
    {"name": "Tirunelveli", "lat": 8.7139, "lon": 77.7567},
    {"name": "Tiruppur", "lat": 11.1085, "lon": 77.3411},
    {"name": "Vellore", "lat": 12.9165, "lon": 79.1325},
    {"name": "Erode", "lat": 11.3410, "lon": 77.7172},
    {"name": "Thoothukudi", "lat": 8.7642, "lon": 78.1348},
    {"name": "Dindigul", "lat": 10.3673, "lon": 77.9803},
    {"name": "Thanjavur", "lat": 10.7870, "lon": 79.1378},
    {"name": "Ranipet", "lat": 12.9296, "lon": 79.3324},
    {"name": "Sivakasi", "lat": 9.4533, "lon": 77.8024},
    {"name": "Karur", "lat": 10.9601, "lon": 78.0766},
    {"name": "Ooty", "lat": 11.4102, "lon": 76.6950},
    {"name": "Hosur", "lat": 12.7409, "lon": 77.8253},
    {"name": "Nagercoil", "lat": 8.1833, "lon": 77.4119},
    {"name": "Kanchipuram", "lat": 12.8342, "lon": 79.7036},
    {"name": "Kumarapalayam", "lat": 11.4422, "lon": 77.7088},
    {"name": "Karaikudi", "lat": 10.0735, "lon": 78.7732},
    {"name": "Neyveli", "lat": 11.5384, "lon": 79.4812},
    {"name": "Cuddalore", "lat": 11.7480, "lon": 79.7714},
    {"name": "Kumbakonam", "lat": 10.9602, "lon": 79.3845},
    {"name": "Tiruvannamalai", "lat": 12.2253, "lon": 79.0747},
    {"name": "Pollachi", "lat": 10.6620, "lon": 77.0065},
    {"name": "Rajapalayam", "lat": 9.4532, "lon": 77.5521},
    {"name": "Gudiyatham", "lat": 12.9472, "lon": 78.8710},
    {"name": "Pudukkottai", "lat": 10.3797, "lon": 78.8208},
    {"name": "Vaniyambadi", "lat": 12.6844, "lon": 78.6158}
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

def generate_logistics_data(num_records=1000, num_cities=30, data_path="data/logistics_data.csv"):
    """
    Generates a synthetic logistics dataset using REAL locations.
    Ensures that every pair of cities is connected to allow direct routes.
    """
    cities = CITIES[:num_cities]
    data = []
    
    # 1. First, ensure EVERY city pair has at least one edge (Direct connection)
    print("Generating base city connectivity...")
    for i in range(len(cities)):
        for j in range(len(cities)):
            if i == j: continue
            
            start = cities[i]
            end = cities[j]
            dist = haversine_distance(start['lat'], start['lon'], end['lat'], end['lon'])
            road_distance = dist * 1.15  # 15% winding road factor
            
            # Create a base record for this pair
            record = {
                "start_location": start['name'],
                "start_lat": start['lat'],
                "start_lon": start['lon'],
                "end_location": end['name'],
                "end_lat": end['lat'],
                "end_lon": end['lon'],
                "distance_km": round(road_distance, 2),
                "delivery_demand": np.random.randint(10, 100),
                "fuel_cost_per_km": round(np.random.uniform(0.12, 0.25), 2),
                "traffic_factor": round(np.random.uniform(1.0, 1.8), 2),
                "time_of_day": np.random.choice(['morning', 'afternoon', 'evening', 'night'])
            }
            data.append(record)

    # 2. Add extra random records to simulate different conditions on the same routes
    print("Adding variety to route conditions...")
    remaining_records = num_records - len(data)
    if remaining_records > 0:
        for _ in range(remaining_records):
            start = np.random.choice(cities)
            end = np.random.choice(cities)
            while start['name'] == end['name']:
                end = np.random.choice(cities)
                
            dist = haversine_distance(start['lat'], start['lon'], end['lat'], end['lon'])
            road_distance = dist * 1.15
            
            record = {
                "start_location": start['name'],
                "start_lat": start['lat'],
                "start_lon": start['lon'],
                "end_location": end['name'],
                "end_lat": end['lat'],
                "end_lon": end['lon'],
                "distance_km": round(road_distance, 2),
                "delivery_demand": np.random.randint(10, 100),
                "fuel_cost_per_km": round(np.random.uniform(0.12, 0.25), 2),
                "traffic_factor": round(np.random.uniform(1.0, 3.0), 2), # More variation
                "time_of_day": np.random.choice(['morning', 'afternoon', 'evening', 'night'])
            }
            data.append(record)

    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    df.to_csv(data_path, index=False)
    print(f"Dataset generated with {len(df)} records. Saved to {data_path}")

if __name__ == '__main__':
    generate_logistics_data(num_records=500)
