import joblib
import random
import pandas as pd
from src.preprocessing import load_and_combine_data, preprocess_data
from src.data_generator import generate_logistics_data
from src.preprocessing import preprocess_data
from src.model import train_and_save_model
from src.evaluation import evaluate_model
from src.optimization import create_graph_from_data, find_optimized_route, find_baseline_route
from src.visualization import visualize_routes, generate_report

def main():
    """
    Main function to run the entire logistics optimization pipeline.
    """
    print("--- Starting Logistics Route Optimization Pipeline ---")

    # Step 1: Generate Data if it doesn't exist
    print("\n[1/7] Generating synthetic data...")
    generate_logistics_data(num_records=500, num_cities=30, data_path="data/logistics_data.csv")

    # Step 2: Preprocess Data
    print("\n[2/7] Preprocessing data...")
    df = pd.read_csv("data/logistics_data.csv")
    X_train, X_test, y_train, y_test, preprocessor, df = preprocess_data(df)


    # Step 3: Train Model
    print("\n[3/7] Training prediction model...")
    model = train_and_save_model(X_train, y_train, preprocessor, model_path="models/delivery_time_predictor.pkl")

    # Step 4: Evaluate Model
    print("\n[4/7] Evaluating model performance...")
    evaluate_model(model, X_test, y_test)

    # Step 5: Optimize a Route
    print("\n[5/7] Optimizing a sample route...")
    graph = create_graph_from_data(df)
    
    # Select a random start and end node for demonstration
    nodes = list(graph.nodes)
    start_node, end_node = random.sample(nodes, 2)
    print(f"Selected route: {start_node} -> {end_node}")

    # Find optimized route using the ML model
    optimized_path, optimized_time = find_optimized_route(graph, model, start_node, end_node)

    # Find baseline route (shortest distance)
    baseline_path, baseline_time = find_baseline_route(graph, start_node, end_node)

    # Step 6: Visualize and Report
    print("\n[6/7] Generating visualization and report...")
    if optimized_path and baseline_path:
        visualize_routes(graph, baseline_path, optimized_path)
        
        results = {
            "start_node": start_node, "end_node": end_node,
            "baseline_path": baseline_path, "baseline_time": baseline_time,
            "optimized_path": optimized_path, "optimized_time": optimized_time
        }
        generate_report(results)
    else:
        print("Could not find a path for the selected nodes.")

    print("\n[7/7] --- Pipeline Finished Successfully ---")

if __name__ == "__main__":
    main()