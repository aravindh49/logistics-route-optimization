from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np

def evaluate_model(model, X_test, y_test):
    """
    Evaluates the performance of the trained model.

    Args:
        model: The trained model pipeline.
        X_test: Test features.
        y_test: Test target.

    Returns:
        dict: A dictionary with evaluation metrics.
    """
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)

    print(f"Model Performance: MAE={mae:.2f} minutes, RMSE={rmse:.2f} minutes")
    
    return {'mae': mae, 'rmse': rmse}
