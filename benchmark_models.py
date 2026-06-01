import argparse
import warnings
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings(
    "ignore",
    message=r"Skipping features without any observed values:.*",
    category=UserWarning,
)

TARGET_COL = "readiness_label"

def prepare_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = df.copy()
    df = df.replace("NA", pd.NA)

    if TARGET_COL not in df.columns:
        raise ValueError(f"Target column '{TARGET_COL}' not found in dataset.")

    y = df[TARGET_COL].astype(str)

    drop_cols = {
        "intern_id", "intern_name", "email", "phone", "linkedin_url",
        "github_profile_url", "github_username", "portfolio_readiness_score",  
        "strength_areas", "improvement_areas", "recommended_actions", TARGET_COL,
        "technical_skills_score", "project_quality_score", "documentation_quality_score",
        "documentation_completeness_score", "business_relevance_score", "presentation_score", "consistency_score",
    }
    feature_cols = [c for c in df.columns if c not in drop_cols]
    X = df[feature_cols].copy()

    numeric_candidates = ["github_repo_count", "num_projects", "tools_used_count"]
    for col in numeric_candidates:
        if col in X.columns:
            X[col] = pd.to_numeric(X[col], errors="coerce")

    return X, y

def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    numeric_cols = X.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = [c for c in X.columns if c not in numeric_cols]

    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_cols),
            ("cat", categorical_pipe, categorical_cols),
        ]
    )

def run_benchmark(df: pd.DataFrame, output_file: Path, test_size: float, random_state: int) -> pd.DataFrame:
    X, y = prepare_data(df)
    preprocessor = build_preprocessor(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y,
    )

    models = {
        "Logistic Regression": LogisticRegression(max_iter=4000, C=0.6, random_state=random_state),
        "Decision Tree": DecisionTreeClassifier(
            random_state=random_state, max_depth=7, min_samples_leaf=4, min_samples_split=10,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, random_state=random_state, max_depth=10, min_samples_leaf=3, min_samples_split=8,
        ),
    }

    rows = []
    for name, model in models.items():
        pipe = Pipeline([("pre", preprocessor), ("model", model)])
        pipe.fit(X_train, y_train)
        train_preds = pipe.predict(X_train)
        test_preds = pipe.predict(X_test)

        train_acc = accuracy_score(y_train, train_preds)
        test_acc = accuracy_score(y_test, test_preds)
        rows.append(
            {
                "model": name,
                "train_accuracy": round(train_acc, 4),
                "test_accuracy": round(test_acc, 4),
                "overfit_gap": round(train_acc - test_acc, 4),
                "test_balanced_accuracy": round(balanced_accuracy_score(y_test, test_preds), 4),
                "test_f1_weighted": round(f1_score(y_test, test_preds, average="weighted"), 4),
            }
        )

    result = pd.DataFrame(rows).sort_values(by="test_accuracy", ascending=False).reset_index(drop=True)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_file, index=False)
    return result

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
        print(f"Error: Base resume CSV file not found in {processed_dir} folder!")
        return
        
    target_file = csv_files[0]
    print(f"Reading data directly from: {target_file.name}")
    raw_df = pd.read_csv(target_file, dtype=str, keep_default_na=False)

    parser = argparse.ArgumentParser(description="Benchmark multiple models and print accuracy table.")
    parser.add_argument(
        "--output-file",
        type=Path,
        default=project_root / "reports" / "model_accuracy_table.csv",
    )
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    table = run_benchmark(
        df=raw_df,
        output_file=args.output_file,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    print("\nModel Benchmark Results")
    print(table.to_string(index=False))
    print(f"\nSaved table: {args.output_file}")

if __name__ == "__main__":
    main()