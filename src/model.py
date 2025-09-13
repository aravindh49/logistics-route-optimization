from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
import joblib
import os

def train_and_save_model(X_train, y_train, preprocessor, model_path="models/delivery_time_predictor.pkl"):
    """
    Trains a machine learning model and saves it.

    Args:
        X_train: Training features.
        y_train: Training target.
        preprocessor: The preprocessing pipeline for features.
        model_path (str): Path to save the trained model.

    Returns:
        The trained model pipeline.
    """
    # Create a full pipeline with preprocessing and the model
    model_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                     ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))])

    # Train the model
    print("Training model...")
    model_pipeline.fit(X_train, y_train)

    # Save the model
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model_pipeline, model_path)
    print(f"Model saved to {model_path}")

    return model_pipeline
