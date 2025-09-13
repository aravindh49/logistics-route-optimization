import pandas as pd
import numpy as np
from faker import Faker
import os

def generate_logistics_data(num_records=200, num_cities=20, data_path="data/logistics_data.csv"):
    """
    Generates a synthetic logistics dataset and saves it to a CSV file.

    Args:
        num_records (int): The number of data records to generate.
        num_cities (int): The number of unique cities.
        data_path (str): The path to save the generated CSV file.
    """
    fake = Faker()
    # Ensure we have enough unique cities
    cities = list(set([fake.city() for _ in range(num_cities * 2)]))
    if len(cities) < num_cities:
        raise ValueError("Could not generate enough unique city names. Please increase the range in the generator.")
    
    selected_cities = np.random.choice(cities, num_cities, replace=False)

    data = []
    for _ in range(num_records):
        start_location, end_location = np.random.choice(selected_cities, 2, replace=False)
        
        record = {
            "start_location": start_location,
            "end_location": end_location,
            "distance_km": np.random.uniform(50, 1000),
            "delivery_demand": np.random.randint(10, 100),
            "fuel_cost_per_km": np.random.uniform(0.1, 0.3),
            "traffic_factor": np.random.uniform(1.0, 2.5), # Multiplier for time based on traffic
            "time_of_day": np.random.choice(['morning', 'afternoon', 'evening', 'night'])
        }
        data.append(record)

    df = pd.DataFrame(data)

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    
    df.to_csv(data_path, index=False)
    print(f"Generated {num_records} records and saved to {data_path}")

if __name__ == '__main__':
    # Example of how to run the generator
    generate_logistics_data(num_records=500, num_cities=30)


