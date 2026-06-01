import argparse
from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

REG_TARGET = "portfolio_readiness_score"

def prepare_clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = df.copy()
    df = df.replace("NA", pd.NA)
    
    if REG_TARGET in df.columns:
        y = pd.to_numeric(df[REG_TARGET], errors="coerce")
        keep = y.notna()
        df = df.loc[keep].copy()
        y = y.loc[keep]
    else:
        y = pd.Series([0] * len(df))

    drop_cols = {
        "intern_id", "intern_name", "email", "phone", "linkedin_url",
        "github_profile_url", "github_username", "readiness_label",
        "strength_areas", "improvement_areas", "recommended_actions",
        REG_TARGET, "technical_skills_score", "project_quality_score",
        "documentation_quality_score", "documentation_completeness_score",
        "business_relevance_score", "presentation_score", "consistency_score",
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
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_cols),
            ("cat", categorical_pipe, categorical_cols),
        ]
    )

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
    csv_files = list(processed_dir.glob("*.csv")) if processed_dir.exists() else []
    
    if not csv_files:
        print("Error: No CSV file found in processed folder!")
        return
        
    target_file = csv_files[0]
    print(f"Extracting features directly from: {target_file.name}")
    raw_df = pd.read_csv(target_file, dtype=str, keep_default_na=False)
    
    X, y = prepare_clean_data(raw_df)
    print(f"Features prepared! Shapes: Features X={X.shape}, Target y={y.shape}")

    df_extracted = X.copy()
    df_extracted[REG_TARGET] = y
    output_path = processed_dir / "extracted_features_output.csv"
    df_extracted.to_csv(output_path, index=False)
    print(f"Cleaned feature data saved to: {output_path}")

if __name__ == "__main__":
    main()