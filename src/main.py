import joblib
import os
import random

from preprocessing import preprocess_data, load_and_combine_data
from model import train_and_save_model
from evaluation import evaluate_model
from optimization import create_graph_from_data, find_optimized_route, find_baseline_route
from visualization import visualize_routes, generate_report

def main():
    """
    Main function to run the entire logistics optimization pipeline.
    """
    print("--- Starting Logistics Route Optimization Pipeline ---")

    # Define the base directory of the project (E:\Logistic_optimization)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Step 1: Load your custom data from the 'Dataset' directory
    print("\n[1/7] Loading custom data...")
    dataset_path = os.path.join(BASE_DIR, "Dataset")
    df = load_and_combine_data(dataset_path)

    # Step 2: Preprocess Data
    print("\n[2/7] Preprocessing data...")
    X_train, X_test, y_train, y_test, preprocessor, df_processed = preprocess_data(df)

    # Step 3: Train Model
    print("\n[3/7] Training prediction model...")
    model = train_and_save_model(X_train, y_train, preprocessor, model_path="models/delivery_time_predictor.pkl")

    # Step 4: Evaluate Model
    print("\n[4/7] Evaluating model performance...")
    evaluate_model(model, X_test, y_test)
    

    # Step 5: Optimize a Route
    print("\n[5/7] Optimizing a sample route...")
    graph = create_graph_from_data(df_processed)
    
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