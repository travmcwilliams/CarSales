#!/usr/bin/env python3
"""
Data Preprocessing Script for Car Sales Price Prediction
Part of the MLOps pipeline for automated data preparation
"""

import pandas as pd
import numpy as np
import re
import argparse
from pathlib import Path
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import joblib

def extract_float(x):
    """Extract float values from mixed data types"""
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float)):
        return float(x)
    m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str(x))
    return float(m.group(0)) if m else np.nan

def preprocess_data(input_path, output_path):
    """
    Preprocess car sales data for machine learning
    
    Args:
        input_path (str): Path to input CSV file
        output_path (str): Path to save processed data
    """
    print("🔄 Starting data preprocessing...")
    
    # Load data
    df = pd.read_csv(input_path)
    print(f"📊 Loaded dataset: {df.shape}")
    
    # Validate required columns
    required_cols = {"Segment", "Kilometers_Driven", "Mileage", "Engine", "Power", "Seats", "price"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Convert numeric columns
    numeric_cols = ["Kilometers_Driven", "Mileage", "Engine", "Power", "Seats", "price"]
    for col in numeric_cols:
        df[col] = df[col].apply(extract_float).astype(float)
    
    # Data cleaning
    initial_size = len(df)
    df = df.dropna(subset=["price"]).copy()
    df = df[(df["price"] > 0) & (df["Kilometers_Driven"] >= 0)]
    final_size = len(df)
    
    print(f"🧹 Data cleaning: {initial_size} → {final_size} rows ({initial_size - final_size} removed)")
    
    # Create preprocessing pipeline
    numeric_features = ["Kilometers_Driven", "Mileage", "Engine", "Power", "Seats"]
    categorical_features = ["Segment"]
    
    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])
    
    preprocessor = ColumnTransformer([
        ("num", numeric_pipe, numeric_features),
        ("cat", categorical_pipe, categorical_features),
    ], remainder="drop")
    
    # Fit and transform data
    X = df[numeric_features + categorical_features]
    y = df["price"]
    
    X_processed = preprocessor.fit_transform(X)
    
    # Save processed data
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save processed features and target
    np.save(output_dir / "X_processed.npy", X_processed)
    np.save(output_dir / "y.npy", y.values)
    
    # Save preprocessor
    joblib.dump(preprocessor, output_dir / "preprocessor.pkl")
    
    # Save feature names
    feature_names = numeric_features + [f"Segment_{cat}" for cat in df["Segment"].unique()]
    np.save(output_dir / "feature_names.npy", feature_names)
    
    # Save metadata
    metadata = {
        "original_shape": df.shape,
        "processed_shape": X_processed.shape,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "target_mean": y.mean(),
        "target_std": y.std(),
        "target_min": y.min(),
        "target_max": y.max()
    }
    
    import json
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Data preprocessing complete!")
    print(f"📁 Processed data saved to: {output_path}")
    print(f"📊 Final shape: {X_processed.shape}")
    print(f"🎯 Target statistics: mean={y.mean():.2f}, std={y.std():.2f}")
    
    return metadata

def main():
    parser = argparse.ArgumentParser(description="Preprocess car sales data")
    parser.add_argument("--input_data", required=True, help="Path to input CSV file")
    parser.add_argument("--output_data", required=True, help="Path to save processed data")
    
    args = parser.parse_args()
    
    try:
        metadata = preprocess_data(args.input_data, args.output_data)
        print("🎉 Preprocessing completed successfully!")
    except Exception as e:
        print(f"❌ Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()
