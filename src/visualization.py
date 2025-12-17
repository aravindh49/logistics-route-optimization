import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import os

def visualize_routes(graph, baseline_path, optimized_path, save_path="reports/route_comparison.png", return_image=False):
    """
    Visualizes the baseline vs. optimized routes on a map.

    Args:
        graph (nx.DiGraph): The graph of locations.
        baseline_path (list): The list of nodes in the baseline path.
        optimized_path (list): The list of nodes in the optimized path.
        save_path (str): Path to save the visualization.
        return_image (bool): If True, returns a BytesIO object of the image.
    """
    pos = nx.spring_layout(graph, seed=42)  # positions for all nodes

    plt.figure(figsize=(16, 12))

    # Draw the full graph
    nx.draw_networkx_nodes(graph, pos, node_size=500, node_color='lightblue')
    nx.draw_networkx_edges(graph, pos, alpha=0.2, edge_color='gray')
    nx.draw_networkx_labels(graph, pos, font_size=8)

    # Highlight the baseline path
    if baseline_path:
        baseline_edges = list(zip(baseline_path, baseline_path[1:]))
        nx.draw_networkx_edges(graph, pos, edgelist=baseline_edges, width=3, edge_color='orange', style='dashed', label='Baseline (Distance-based)')

    # Highlight the optimized path
    if optimized_path:
        optimized_edges = list(zip(optimized_path, optimized_path[1:]))
        nx.draw_networkx_edges(graph, pos, edgelist=optimized_edges, width=4, edge_color='green', label='Optimized (ML-based)')

    plt.title("Logistics Route Comparison: Baseline vs. Optimized")
    plt.legend()
    plt.axis('off')
    
    if return_image:
        import io
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        plt.close()
        img_buffer.seek(0)
        return img_buffer
    else:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        plt.close()
        print(f"Route visualization saved to {save_path}")

def generate_report(results, report_path="reports/optimization_report.csv"):
    """
    Generates a CSV report of the optimization results.

    Args:
        results (dict): A dictionary containing the results.
        report_path (str): Path to save the CSV report.
    """
    if results['optimized_time'] is not None and results['baseline_time'] is not None:
        time_savings = results['baseline_time'] - results['optimized_time']
        time_savings_percent = (time_savings / results['baseline_time']) * 100 if results['baseline_time'] > 0 else 0
    else:
        time_savings = 0
        time_savings_percent = 0

    report_data = {
        "Start Node": [results['start_node']],
        "End Node": [results['end_node']],
        "Baseline Path": [str(results['baseline_path'])],
        "Baseline Time (minutes)": [results['baseline_time']],
        "Optimized Path": [str(results['optimized_path'])],
        "Optimized Time (minutes)": [results['optimized_time']],
        "Time Saved (minutes)": [time_savings],
        "Efficiency Improvement (%)": [time_savings_percent]
    }
    
    df_report = pd.DataFrame(report_data)
    df_report.to_csv(report_path, index=False)
    print(f"Optimization report saved to {report_path}")
