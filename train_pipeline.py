import argparse
import sys
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

sys.path.append(str(Path(__file__).resolve().parent))
from extract_features import prepare_clean_data, build_preprocessor

def run_regression_pipeline(df: pd.DataFrame, model_file: Path, report_file: Path, test_size: float, random_state: int) -> pd.DataFrame:
    X, y = prepare_clean_data(df)
    preprocessor = build_preprocessor(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    pipe = Pipeline([("pre", preprocessor), ("model", RandomForestRegressor(n_estimators=200, random_state=random_state, max_depth=10, min_samples_leaf=4))])
    pipe.fit(X_train, y_train)
    
    train_preds = pipe.predict(X_train)
    test_preds = pipe.predict(X_test)

    train_rmse = mean_squared_error(y_train, train_preds) ** 0.5
    test_rmse = mean_squared_error(y_test, test_preds) ** 0.5
    
    rows = [{
        "model": "Random Forest Regressor",
        "train_rmse": round(train_rmse, 4),
        "test_rmse": round(test_rmse, 4),
        "train_r2": round(r2_score(y_train, train_preds), 4),
        "test_r2": round(r2_score(y_test, test_preds), 4),
    }]

    model_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, model_file)

    print("\nScaling Intern Scores to 1-10 Job Readiness Scale...")
    df_scored = df.copy()
    all_predictions = pipe.predict(X)
    
    min_p, max_p = all_predictions.min(), all_predictions.max()
    if max_p - min_p == 0:
        scaled_scores = np.full_like(all_predictions, 5.0)
    else:
        scaled_scores = 1 + (all_predictions - min_p) * (10 - 1) / (max_p - min_p)
        
    df_scored["predicted_readiness_score_1_to_10"] = np.round(scaled_scores, 1)

    preview = df_scored[["intern_name", "predicted_readiness_score_1_to_10"]].sort_values(
        by="predicted_readiness_score_1_to_10", ascending=False
    )
    print("\n--- Top 10 Job-Ready Interns Preview ---")
    print(preview.head(10).to_string(index=False))

    report_file.parent.mkdir(parents=True, exist_ok=True)
    df_scored.to_csv(report_file, index=False)
    return pd.DataFrame(rows)

def main() -> None:
    project_root = None
    current_dir = Path(__file__).resolve()
    for parent in current_dir.parents:
        if "Graphura Resume Rediness Score" in parent.name:
            project_root = parent
            break
    if project_root is None:
        project_root = current_dir.parents[2]

    processed_dir = project_root / "data" / "processed"
    
   
    csv_files = [f for f in processed_dir.glob("*.csv") if "extracted_features_output" not in f.name] if processed_dir.exists() else []
    
    if not csv_files:
        print("Error: Base resume CSV file not found in processed folder!")
        return
        
    target_file = csv_files[0]
    print(f"Training final pipeline using: {target_file.name}")
    raw_df = pd.read_csv(target_file, dtype=str, keep_default_na=False)

    parser = argparse.ArgumentParser(description="Train ML pipeline and output 1-10 scores.")
    parser.add_argument(
        "--model-file",
        type=Path,
        default=project_root / "models" / "readiness_regression_model.pkl",
    )
    parser.add_argument(
        "--report-file",
        type=Path,
        default=project_root / "reports" / "intern_readiness_1_to_10_scores.csv",
    )
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    table = run_regression_pipeline(
        df=raw_df,
        model_file=args.model_file,
        report_file=args.report_file,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    print("\nModel Training Results")
    print(table.to_string(index=False))
    print(f"\nSaved final scored table: {args.report_file}")

if __name__ == "__main__":
    main()