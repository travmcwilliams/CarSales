#!/usr/bin/env python3
"""
Azure ML Training Script for Car Sales Price Prediction
Optimized for Azure ML execution environment
"""

import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import argparse

def compute_rmse(y_true, y_pred):
    """Compute Root Mean Square Error"""
    return np.sqrt(mean_squared_error(y_true, y_pred))

def train_model_azure(input_path, output_path):
    """
    Train Random Forest model for car price prediction in Azure ML
    """
    print("🔄 Starting Azure ML model training...")
    
    # Load data
    df = pd.read_csv(input_path)
    print(f"📊 Loaded dataset: {df.shape}")
    
    # Data preprocessing
    num_features = ["Kilometers_Driven", "Mileage", "Engine", "Power", "Seats"]
    cat_features = ["Segment"]
    
    # Create preprocessing pipeline
    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])
    
    preprocessor = ColumnTransformer([
        ("num", numeric_pipe, num_features),
        ("cat", categorical_pipe, cat_features),
    ], remainder="drop")
    
    # Prepare data
    X = df[num_features + cat_features].copy()
    y = df["price"].copy()
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"📈 Training set: {X_train.shape}")
    print(f"📊 Test set: {X_test.shape}")
    
    # Create and train model
    model = Pipeline([
        ("preprocessor", preprocessor),
        ("model", RandomForestRegressor(n_estimators=200, random_state=42))
    ])
    
    # Hyperparameter tuning
    param_grid = {
        "model__n_estimators": [100, 200],
        "model__max_depth": [None, 10, 20],
        "model__min_samples_split": [2, 5]
    }
    
    grid_search = GridSearchCV(
        estimator=model,
        param_grid=param_grid,
        scoring="neg_root_mean_squared_error",
        cv=3,
        n_jobs=-1
    )
    
    print("🔍 Starting hyperparameter tuning...")
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    best_pred = best_model.predict(X_test)
    
    # Calculate metrics
    rmse = compute_rmse(y_test, best_pred)
    mae = mean_absolute_error(y_test, best_pred)
    r2 = r2_score(y_test, best_pred)
    
    print(f"\n🏆 Model Performance:")
    print(f"  RMSE: {rmse:.3f}")
    print(f"  MAE: {mae:.3f}")
    print(f"  R²: {r2:.3f}")
    print(f"  Best Parameters: {grid_search.best_params_}")
    
    # Save model
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(best_model, output_dir / "model.pkl")
    
    # Save metrics
    metrics = {
        "rmse": float(rmse),
        "mae": float(mae),
        "r2": float(r2),
        "best_params": grid_search.best_params_
    }
    
    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    # Save feature importance
    feature_names = num_features + [f"Segment_{cat}" for cat in df["Segment"].unique()]
    feature_importance = pd.DataFrame({
        "feature": feature_names,
        "importance": best_model.named_steps["model"].feature_importances_
    }).sort_values("importance", ascending=False)
    
    feature_importance.to_csv(output_dir / "feature_importance.csv", index=False)
    
    print(f"✅ Model saved to: {output_path}")
    print(f"📊 Performance metrics saved")
    
    return metrics

def main():
    parser = argparse.ArgumentParser(description="Train car sales price prediction model in Azure ML")
    parser.add_argument("--input_data", required=True, help="Path to input CSV file")
    parser.add_argument("--output_model", required=True, help="Path to save trained model")
    
    args = parser.parse_args()
    
    try:
        metrics = train_model_azure(args.input_data, args.output_model)
        print("🎉 Training completed successfully!")
        return metrics
    except Exception as e:
        print(f"❌ Training failed: {e}")
        raise

if __name__ == "__main__":
    main()
