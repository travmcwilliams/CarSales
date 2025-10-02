#!/usr/bin/env python3
"""
Model Registration Script for Car Sales Price Prediction
Part of the MLOps pipeline for automated model registration and deployment
"""

import argparse
import json
import joblib
import mlflow
import mlflow.sklearn
from pathlib import Path
from mlflow.models.signature import infer_signature
import pandas as pd
import numpy as np

def register_model(model_path, model_name):
    """
    Register trained model in MLflow and Azure ML
    
    Args:
        model_path (str): Path to trained model
        model_name (str): Name for the registered model
    """
    print("🔄 Starting model registration...")
    
    model_dir = Path(model_path)
    
    # Load model and components
    complete_pipeline = joblib.load(model_dir / "model.pkl")
    best_model = joblib.load(model_dir / "best_model.pkl")
    preprocessor = joblib.load(model_dir / "preprocessor.pkl")
    
    # Load evaluation results
    with open(model_dir / "evaluation_results.json", "r") as f:
        evaluation_results = json.load(f)
    
    # Load feature importance
    feature_importance = pd.read_csv(model_dir / "feature_importance.csv")
    
    print(f"📊 Model loaded from: {model_path}")
    print(f"🏆 Best RMSE: {evaluation_results['best_metrics']['rmse']:.3f}")
    print(f"📈 R² Score: {evaluation_results['best_metrics']['r2']:.3f}")
    
    # Set up MLflow
    mlflow.set_experiment("CarSales")
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=f"register_{model_name}"):
        # Set tags
        mlflow.set_tags({
            "project": "CarSales",
            "pipeline_stage": "register",
            "framework": "sklearn",
            "target": "price",
            "model_type": "RandomForestRegressor",
            "model_name": model_name
        })
        
        # Log metrics
        mlflow.log_metrics(evaluation_results["best_metrics"])
        mlflow.log_metrics({
            "improvement_percent": evaluation_results["improvement_percent"]
        })
        
        # Log parameters
        mlflow.log_params(evaluation_results["best_params"])
        
        # Create signature for model
        # Generate sample input data
        sample_features = [
            "Kilometers_Driven", "Mileage", "Engine", "Power", "Seats",
            "Segment_luxury", "Segment_non-luxury segment"
        ]
        
        # Create sample data that matches the expected input format
        sample_data = pd.DataFrame({
            "Kilometers_Driven": [50000, 75000, 30000],
            "Mileage": [15.0, 20.0, 12.0],
            "Engine": [1500, 2000, 1200],
            "Power": [100, 150, 80],
            "Seats": [5, 7, 5],
            "Segment": ["luxury", "non-luxury segment", "luxury"]
        })
        
        # Transform sample data to get the right format
        sample_processed = preprocessor.transform(sample_data)
        sample_predictions = best_model.predict(sample_processed)
        
        # Create signature
        signature = infer_signature(sample_processed, sample_predictions)
        
        # Log model
        mlflow.sklearn.log_model(
            sk_model=complete_pipeline,
            artifact_path="model",
            signature=signature,
            input_example=sample_data,
            registered_model_name=model_name
        )
        
        # Log artifacts
        mlflow.log_artifacts(str(model_dir), artifact_path="model_artifacts")
        
        # Log feature importance as artifact
        feature_importance.to_csv("feature_importance.csv", index=False)
        mlflow.log_artifact("feature_importance.csv")
        
        # Log evaluation results
        with open("evaluation_results.json", "w") as f:
            json.dump(evaluation_results, f, indent=2)
        mlflow.log_artifact("evaluation_results.json")
        
        # Register model
        model_uri = f"runs:/{mlflow.active_run().info.run_id}/model"
        
        try:
            mv = mlflow.register_model(model_uri=model_uri, name=model_name)
            print(f"✅ Model registered successfully: {model_name} v{mv.version}")
            print(f"🔗 Model URI: {model_uri}")
            
            # Log registration info
            mlflow.set_tags({
                "registered_model_name": model_name,
                "model_version": mv.version,
                "model_uri": model_uri
            })
            
        except Exception as e:
            print(f"⚠️ Model registration failed: {e}")
            print("Model artifacts logged to run")
        
        # Model validation
        print("\n🔍 Model Validation:")
        
        # Test model loading
        try:
            loaded_model = mlflow.sklearn.load_model(model_uri)
            test_prediction = loaded_model.predict(sample_data)
            print(f"✅ Model loading test passed")
            print(f"📊 Sample prediction: {test_prediction[0]:.2f}")
        except Exception as e:
            print(f"❌ Model loading test failed: {e}")
        
        # Performance validation
        rmse = evaluation_results["best_metrics"]["rmse"]
        r2 = evaluation_results["best_metrics"]["r2"]
        
        if rmse < 10.0 and r2 > 0.8:
            print("✅ Performance validation passed")
            print(f"  RMSE: {rmse:.3f} (< 10.0)")
            print(f"  R²: {r2:.3f} (> 0.8)")
        else:
            print("⚠️ Performance validation warning")
            print(f"  RMSE: {rmse:.3f} (should be < 10.0)")
            print(f"  R²: {r2:.3f} (should be > 0.8)")
        
        print(f"\n📋 Registration Summary:")
        print(f"  Model Name: {model_name}")
        print(f"  Run ID: {mlflow.active_run().info.run_id}")
        print(f"  Model URI: {model_uri}")
        print(f"  Performance: RMSE={rmse:.3f}, R²={r2:.3f}")
        
        return {
            "model_name": model_name,
            "model_uri": model_uri,
            "run_id": mlflow.active_run().info.run_id,
            "performance": evaluation_results["best_metrics"]
        }

def main():
    parser = argparse.ArgumentParser(description="Register car sales price prediction model")
    parser.add_argument("--model_path", required=True, help="Path to trained model")
    parser.add_argument("--model_name", required=True, help="Name for the registered model")
    
    args = parser.parse_args()
    
    try:
        result = register_model(args.model_path, args.model_name)
        print("🎉 Model registration completed successfully!")
        return result
    except Exception as e:
        print(f"❌ Model registration failed: {e}")
        raise

if __name__ == "__main__":
    main()
