import argparse
from pathlib import Path
import warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, MinMaxScaler


warnings.filterwarnings("ignore", category=UserWarning)

CLASS_TARGET = "readiness_label"
REG_TARGET = "portfolio_readiness_score"

def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    
    num_cols = X.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = [c for c in X.columns if c not in num_cols]
    
    return ColumnTransformer(
        transformers=[
           
            ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num_cols),
            ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")), ("oh", OneHotEncoder(handle_unknown="ignore"))]), cat_cols),
        ]
    )

def prepare_data(df: pd.DataFrame, is_regression=False) -> tuple[pd.DataFrame, pd.Series]:
   
    drop_cols = {
        "intern_id", "intern_name", "email", "phone", "linkedin_url",
        "github_profile_url", "github_username", "strength_areas", 
        "improvement_areas", "recommended_actions", "readiness_label",
        "portfolio_readiness_score", "technical_skills_score", 
        "project_quality_score", "documentation_quality_score", 
        "documentation_completeness_score", "business_relevance_score", 
        "presentation_score", "consistency_score"
    }
    
   
    X = df[[c for c in df.columns if c not in drop_cols]].copy()
    
   
    for c in ["github_repo_count", "num_projects", "tools_used_count"]:
        if c in X.columns:
            X[c] = pd.to_numeric(X[c], errors="coerce")
            
    target = REG_TARGET if is_regression else CLASS_TARGET
    y = pd.to_numeric(df[target], errors="coerce") if is_regression else df[target].astype(str)
    
    return X, y

def main() -> None:
    project_root = Path(__file__).resolve().parent
    
   
    input_file = project_root / "data" / "processed" / "final_extracted_resume.csv"
    df = pd.read_csv(input_file, dtype=str, keep_default_na=False).replace("NA", pd.NA)

    
    X_reg, y_reg = prepare_data(df, is_regression=True)
    X_train, X_test, y_train, y_test = train_test_split(X_reg, y_reg, test_size=0.2, random_state=42)
    
    preprocessor = build_preprocessor(X_reg)
    
   
    model = Pipeline([
        ("pre", preprocessor),
        ("model", RandomForestRegressor(
            n_estimators=500, 
            max_depth=15, 
            min_samples_split=5, 
            random_state=42
        ))
    ])
    
    model.fit(X_train, y_train)
    
   
    raw_preds = model.predict(X_reg)
    
   
    scaler = MinMaxScaler(feature_range=(1, 10))
    scaled_scores = scaler.fit_transform(raw_preds.reshape(-1, 1))
    
   
    df["predicted_readiness_score_1_to_10"] = np.round(scaled_scores, 1)

   
    output_path = project_root / "reports" / "intern_readiness_1_to_10_scores.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
   
    print("\n--- Final Accurate Readiness Leaderboard ---")
    preview = df[["intern_name", "predicted_readiness_score_1_to_10"]].sort_values(
        by="predicted_readiness_score_1_to_10", ascending=False
    )
    print(preview.head(10).to_string(index=False))
    print(f"\nResults saved to: {output_path}")

if __name__ == "__main__":
    main()