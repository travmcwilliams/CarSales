#!/usr/bin/env python3
"""
Model Training Script for Car Sales Price Prediction
Part of the MLOps pipeline for automated model training and evaluation
"""

import numpy as np
import pandas as pd
import argparse
import json
from pathlib import Path
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import mlflow
import mlflow.sklearn
from mlflow.models.signature import infer_signature

def compute_rmse(y_true, y_pred):
    """Compute Root Mean Square Error"""
    return np.sqrt(mean_squared_error(y_true, y_pred))

def train_model(input_path, output_path):
    """
    Train Random Forest model for car price prediction
    
    Args:
        input_path (str): Path to processed data
        output_path (str): Path to save trained model
    """
    print("🔄 Starting model training...")
    
    # Load processed data
    input_dir = Path(input_path)
    X_processed = np.load(input_dir / "X_processed.npy")
    y = np.load(input_dir / "y.npy")
    preprocessor = joblib.load(input_dir / "preprocessor.pkl")
    feature_names = np.load(input_dir / "feature_names.npy")
    
    # Load metadata
    with open(input_dir / "metadata.json", "r") as f:
        metadata = json.load(f)
    
    print(f"📊 Loaded processed data: {X_processed.shape}")
    print(f"🎯 Target range: {y.min():.2f} - {y.max():.2f}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y, test_size=0.2, random_state=42
    )
    
    print(f"📈 Training set: {X_train.shape}")
    print(f"📊 Test set: {X_test.shape}")
    
    # Set up MLflow
    mlflow.set_experiment("CarSales")
    mlflow.autolog(disable=True)  # Manual control
    
    with mlflow.start_run(run_name="car_sales_training"):
        # Create baseline model
        baseline_model = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )
        
        # Train baseline
        baseline_model.fit(X_train, y_train)
        baseline_pred = baseline_model.predict(X_test)
        
        baseline_rmse = compute_rmse(y_test, baseline_pred)
        baseline_mae = mean_absolute_error(y_test, baseline_pred)
        baseline_r2 = r2_score(y_test, baseline_pred)
        
        print(f"📊 Baseline Performance:")
        print(f"  RMSE: {baseline_rmse:.3f}")
        print(f"  MAE: {baseline_mae:.3f}")
        print(f"  R²: {baseline_r2:.3f}")
        
        # Hyperparameter tuning
        param_grid = {
            "n_estimators": [100, 200, 300],
            "max_depth": [None, 10, 20, 30],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf": [1, 2, 4]
        }
        
        print("🔍 Starting hyperparameter tuning...")
        grid_search = GridSearchCV(
            estimator=RandomForestRegressor(random_state=42, n_jobs=-1),
            param_grid=param_grid,
            scoring="neg_root_mean_squared_error",
            cv=3,
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        # Best model
        best_model = grid_search.best_estimator_
        best_pred = best_model.predict(X_test)
        
        best_rmse = compute_rmse(y_test, best_pred)
        best_mae = mean_absolute_error(y_test, best_pred)
        best_r2 = r2_score(y_test, best_pred)
        
        print(f"🏆 Best Model Performance:")
        print(f"  Best Parameters: {grid_search.best_params_}")
        print(f"  RMSE: {best_rmse:.3f}")
        print(f"  MAE: {best_mae:.3f}")
        print(f"  R²: {best_r2:.3f}")
        print(f"  Improvement: {((baseline_rmse - best_rmse) / baseline_rmse * 100):.1f}%")
        
        # Create complete pipeline
        from sklearn.pipeline import Pipeline
        complete_pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("model", best_model)
        ])
        
        # Log to MLflow
        mlflow.set_tags({
            "project": "CarSales",
            "pipeline_stage": "train",
            "framework": "sklearn",
            "target": "price",
            "model_type": "RandomForestRegressor"
        })
        
        mlflow.log_metrics({
            "baseline_rmse": baseline_rmse,
            "baseline_mae": baseline_mae,
            "baseline_r2": baseline_r2,
            "best_rmse": best_rmse,
            "best_mae": best_mae,
            "best_r2": best_r2,
            "improvement_percent": ((baseline_rmse - best_rmse) / baseline_rmse * 100)
        })
        
        mlflow.log_params(grid_search.best_params_)
        
        # Create signature
        sample_data = pd.DataFrame(X_train[:5], columns=feature_names)
        signature = infer_signature(sample_data, best_model.predict(X_train[:5]))
        
        # Save model
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save complete pipeline
        joblib.dump(complete_pipeline, output_dir / "model.pkl")
        
        # Save individual components
        joblib.dump(best_model, output_dir / "best_model.pkl")
        joblib.dump(preprocessor, output_dir / "preprocessor.pkl")
        
        # Save feature importance
        feature_importance = pd.DataFrame({
            "feature": feature_names,
            "importance": best_model.feature_importances_
        }).sort_values("importance", ascending=False)
        
        feature_importance.to_csv(output_dir / "feature_importance.csv", index=False)
        
        # Save evaluation results
        evaluation_results = {
            "baseline_metrics": {
                "rmse": baseline_rmse,
                "mae": baseline_mae,
                "r2": baseline_r2
            },
            "best_metrics": {
                "rmse": best_rmse,
                "mae": best_mae,
                "r2": best_r2
            },
            "best_params": grid_search.best_params_,
            "improvement_percent": ((baseline_rmse - best_rmse) / baseline_rmse * 100),
            "feature_importance": feature_importance.to_dict("records")
        }
        
        with open(output_dir / "evaluation_results.json", "w") as f:
            json.dump(evaluation_results, f, indent=2)
        
        # Save sample predictions
        sample_predictions = pd.DataFrame({
            "actual": y_test[:10],
            "predicted": best_pred[:10],
            "error": best_pred[:10] - y_test[:10],
            "error_percent": ((best_pred[:10] - y_test[:10]) / y_test[:10] * 100)
        })
        
        sample_predictions.to_csv(output_dir / "sample_predictions.csv", index=False)
        
        print(f"✅ Model training complete!")
        print(f"📁 Model saved to: {output_path}")
        print(f"🏆 Best RMSE: {best_rmse:.3f}")
        print(f"📈 R² Score: {best_r2:.3f}")
        
        return evaluation_results

def main():
    parser = argparse.ArgumentParser(description="Train car sales price prediction model")
    parser.add_argument("--input_data", required=True, help="Path to processed data")
    parser.add_argument("--output_model", required=True, help="Path to save trained model")
    
    args = parser.parse_args()
    
    try:
        results = train_model(args.input_data, args.output_model)
        print("🎉 Model training completed successfully!")
    except Exception as e:
        print(f"❌ Model training failed: {e}")
        raise

if __name__ == "__main__":
    main()
