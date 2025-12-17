import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import os
import glob
import numpy as np

def parse_vrp_file(filepath):
    """
    Parses a single VRP benchmark file (Solomon format).
    Extracts customer locations, demand, and time windows.
    """
    with open(filepath, 'r') as f:
        content = f.readlines()

    # Find where the customer data starts
    data_start_index = -1
    for i, line in enumerate(content):
        if "CUST NO." in line.upper():
            data_start_index = i + 1
            break
    
    if data_start_index == -1:
        return None # Or raise an error if the format is unexpected

    # Read the data into a DataFrame, splitting by whitespace
    data_rows = [line.split() for line in content[data_start_index:] if line.strip()]
    df = pd.DataFrame(data_rows, columns=['cust_no', 'x_coord', 'y_coord', 'demand', 'ready_time', 'due_date', 'service_time'])

    # Convert columns to numeric types
    for col in df.columns:
        df[col] = pd.to_numeric(df[col])

    return df

def create_links_from_nodes(node_df):
    """
    Creates a DataFrame of all possible links (edges) between nodes.
    Calculates Euclidean distance and simulates other required features.
    """
    links = []
    for i, start_node in node_df.iterrows():
        for j, end_node in node_df.iterrows():
            if i == j:
                continue # No self-loops
            distance = np.sqrt((start_node['x_coord'] - end_node['x_coord'])**2 + (start_node['y_coord'] - end_node['y_coord'])**2)
            links.append({
                "start_location": f"C_{int(start_node['cust_no'])}",
                "end_location": f"C_{int(end_node['cust_no'])}",
                "distance_km": distance,
                "delivery_demand": end_node['demand'],
                "fuel_cost_per_km": np.random.uniform(0.1, 0.3), # Simulate feature
                "traffic_factor": np.random.uniform(1.0, 2.5), # Simulate feature
                "time_of_day": np.random.choice(['morning', 'afternoon', 'evening', 'night']) # Simulate feature
            })
    return pd.DataFrame(links)

def load_and_combine_data(data_directory):
    """
    Loads and combines all .txt files from a given directory into a single DataFrame.
    
    Args:
        data_directory (str): The path to the directory containing .txt data files.

    Returns:
        pd.DataFrame: A single DataFrame containing all the data.
    """
    txt_files = glob.glob(os.path.join(data_directory, "*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No .txt files found in the directory: {data_directory}")
    
    print(f"Found {len(txt_files)} files to load: {txt_files}")
    
    # We will process the first file found for this example.
    # You could extend this to combine nodes from all files if needed.
    first_file = txt_files[0]
    print(f"Parsing VRP data from: {first_file}")
    node_df = parse_vrp_file(first_file)

    if node_df is None:
        raise ValueError(f"Could not parse VRP data from file: {first_file}")

    print("Creating links between nodes and simulating features...")
    links_df = create_links_from_nodes(node_df)
    return links_df

def preprocess_data(df):
    """
    Loads and preprocesses the logistics data.

    Args:
        df (pd.DataFrame): The DataFrame to preprocess.

    Returns:
        tuple: A tuple containing:
            - X_train, X_test, y_train, y_test (split data)
            - preprocessor (the fitted preprocessor object)
            - df (the original dataframe with new features)
    """
    # Feature Engineering
    df['estimated_cost'] = df['distance_km'] * df['fuel_cost_per_km']
    df['base_time_minutes'] = df['distance_km']  # distance in km
    df['estimated_time_minutes'] = (df['base_time_minutes'] / 60) * df['traffic_factor'] * 60


    # Define features (X) and target (y)
    # We predict 'estimated_time_minutes'
    y = df['estimated_time_minutes']
    X = df[['distance_km', 'delivery_demand', 'traffic_factor', 'time_of_day']]

    # Define preprocessing for numeric and categorical features
    numeric_features = ['distance_km', 'delivery_demand', 'traffic_factor']
    categorical_features = ['time_of_day']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(), categorical_features)])

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    return X_train, X_test, y_train, y_test, preprocessor, df
