import http
import json
import os
from pathlib import Path
from datetime import datetime, timezone

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from shared.http.json_client import fetch_url

import joblib

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = Path(os.getenv("MODEL_BASE_DIR", str(PROJECT_ROOT / "models")))
LATEST_METADATA_PATH = MODEL_DIR / "latest.json"


FEATURE_COLS = [
    "avg_pts_last3",
    "avg_min_last3",
    "avg_pts_last5",
    "avg_min_last5",
    "expected_goals",
    "expected_assists",
    "avg_xgi_last5",
    "expected_goals_conceded",
    "clean_sheets_last5",
    "saves",
    "bps",
    "next_team_difficulty",
    "next_opponent_difficulty"
]

# --- Config parameters ---
TARGET_COL = "target_next_gw"
S2_BASE_URL = os.getenv("S2_BASE_URL", "http://localhost:8001").strip()

TRAIN_SPLIT_RATIO = float(os.getenv("TRAIN_SPLIT_RATIO", "0.7"))
TRAIN_RANDOM_SEED = int(os.getenv("TRAIN_RANDOM_SEED", "42"))
RF_N_ESTIMATORS = int(os.getenv("RF_N_ESTIMATORS", "300"))
RF_MAX_DEPTH = int(os.getenv("RF_MAX_DEPTH", "10"))
RF_MIN_SAMPLES_LEAF = int(os.getenv("RF_MIN_SAMPLES_LEAF", "5"))
BASELINE_STRATEGY = os.getenv("BASELINE_STRATEGY", "mean").strip()


def load_feature_dataset():
    if not S2_BASE_URL:
        raise RuntimeError("S2_BASE_URL is required for trainer feature loading")

    payload = fetch_url(S2_BASE_URL, "/training-dataset")
    data = payload.get("data", [])
    df = pd.DataFrame(data)

    dataset_metadata = {
        "service": "S2",
        "base_url": S2_BASE_URL,
        "source_endpoint": payload.get("source_endpoint", "/training-dataset"),
        "feature_table": payload.get("feature_table"),
        "row_count": payload.get("row_count", len(df)),
        "columns": payload.get("columns", list(df.columns)),
    }

    return df, dataset_metadata


# ---- Rolling GW split (season-aware) ----
def rolling_gw_split(df, split_ratio=0.7, logs=False):
    """
    In every season, split the data by gameweek:
        train: GW <= 70%
        test : GW > 70%
        - every player has history in the train set, but not necessarily in the test set
    """

    train_parts = []
    test_parts = []
    split_summary = []

    for season, season_df in df.groupby("season"):

        max_gw = season_df["GW"].max()
        split_gw = int(max_gw * split_ratio)

        train_part = season_df[season_df["GW"] <= split_gw]
        test_part = season_df[season_df["GW"] > split_gw]

        train_parts.append(train_part)
        test_parts.append(test_part)
        split_summary.append({
            "season": season,
            "max_gw": int(max_gw),
            "split_gw": int(split_gw),
            "train_rows": int(len(train_part)),
            "test_rows": int(len(test_part)),
        })

        if logs:
            print(f"{season}: max_gw={max_gw}, split_gw={split_gw}")

    train_df = pd.concat(train_parts)
    test_df = pd.concat(test_parts)

    return train_df, test_df, split_summary


def validate_split_order(train_df: pd.DataFrame, test_df: pd.DataFrame):
    season_checks = []

    for season in sorted(set(train_df["season"]).intersection(set(test_df["season"]))):
        train_season = train_df[train_df["season"] == season]
        test_season = test_df[test_df["season"] == season]

        max_train_gw = int(train_season["GW"].max())
        min_test_gw = int(test_season["GW"].min())
        is_time_ordered = max_train_gw < min_test_gw

        if not is_time_ordered:
            raise RuntimeError(
                f"Train/test split order check failed for season {season}: "
                f"max_train_gw={max_train_gw}, min_test_gw={min_test_gw}"
            )

        season_checks.append({
            "season": season,
            "max_train_gw": max_train_gw,
            "min_test_gw": min_test_gw,
            "is_time_ordered": is_time_ordered,
        })

    return {
        "is_time_ordered": True,
        "season_checks": season_checks,
    }


# ---- Metrics ----
def mae(y_true, y_pred):
    return sum(abs(a - b) for a, b in zip(y_true, y_pred)) / max(1, len(y_true))

def rmse(y_true, y_pred):
    return (sum((a - b) ** 2 for a, b in zip(y_true, y_pred)) / max(1, len(y_true))) ** 0.5
 
# ---- Evaluation helper ----
def evaluate_model(model, X_train, y_train, X_test, y_test):

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5

    return {
        "y_pred": y_pred,
        "MAE": #mae(y_test, y_pred) 
        mae,
        "RMSE": #rmse(y_test, y_pred)
        rmse
    }


def create_version_dir():
    version = datetime.now(timezone.utc).strftime("v%Y%m%d_%H%M%S")
    version_dir = MODEL_DIR / version
    version_dir.mkdir(parents=True, exist_ok=False)
    return version, version_dir


def write_json_atomic(path: Path, payload: dict):
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    tmp_path.replace(path)

def main(logs=True):

    df, dataset_metadata = load_feature_dataset()
    # ---- last gameweek drop ----
    df = df.dropna(subset=[TARGET_COL, "next_opponent_difficulty"])

    #df_model = df.dropna(subset=["avg_pts_last5"])
    #df_model = df_model[df_model["avg_min_last5"] >= 0.0]

    split_ratio = TRAIN_SPLIT_RATIO
    train_df, test_df, split_summary = rolling_gw_split(df, split_ratio=split_ratio, logs=logs)
    split_validation = validate_split_order(train_df, test_df)

    X_train = train_df[FEATURE_COLS]   
    y_train = train_df[TARGET_COL]
    
    X_test = test_df[FEATURE_COLS]
    y_test = test_df[TARGET_COL]

    # --- Feature Scaling ---
    scaler = StandardScaler()
    scaler.fit(X_train)
    
    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)    

    print("Train rows:", len(train_df))
    print("Test rows :", len(test_df))

    if len(y_train) < 20 or len(y_test) < 10:
        print("Tul keves adat.")
        return

    # ---- Linear Regression ----
    lr = LinearRegression()
    lr_results = evaluate_model(lr, X_train_scaled, y_train, X_test_scaled, y_test)

    # ---- Random Forest Regressor ----
    rf = RandomForestRegressor(
        n_estimators=RF_N_ESTIMATORS,
        random_state=TRAIN_RANDOM_SEED,
        max_depth=RF_MAX_DEPTH,
        min_samples_leaf=RF_MIN_SAMPLES_LEAF,
    )
    rf_results = evaluate_model(rf, X_train, y_train, X_test, y_test)

    # ---- Mean Baseline ----
    baseline = DummyRegressor(strategy=BASELINE_STRATEGY)
    baseline_results = evaluate_model(baseline, X_train, y_train, X_test, y_test)

    models = {
        "lr": lr_results,
        "rf": rf_results,
        "baseline": baseline_results
    }

    best_model_name = min(models, key=lambda m: models[m]["MAE"])

    model_objects = {
        "lr": lr,
        "rf": rf,
        "baseline": baseline
    }
    
    best_model = model_objects[best_model_name]

    # ---- Save versioned artifacts ----
    MODEL_DIR.mkdir(exist_ok=True)
    version, version_dir = create_version_dir()

    joblib.dump(lr, version_dir / "linear_regression.joblib")
    joblib.dump(rf, version_dir / "random_forest.joblib")
    joblib.dump(baseline, version_dir / "baseline.joblib")
    joblib.dump(scaler, version_dir / "scaler.joblib")
    joblib.dump(best_model, version_dir / "production_model.joblib")

    print(f"LinearRegression  -> MAE: {lr_results['MAE']:.3f}, RMSE: {lr_results['RMSE']:.3f}")
    print(f"RandomForestRegressor -> MAE: {rf_results['MAE']:.3f}, RMSE: {rf_results['RMSE']:.3f}")
    print(f"MeanBaseline      -> MAE: {baseline_results['MAE']:.3f}, RMSE: {baseline_results['RMSE']:.3f}")

    print(
        f"\nBest model: {best_model_name} "
        f"with MAE: {models[best_model_name]['MAE']:.3f}"
    )

    improvement_lr = baseline_results["MAE"] - lr_results["MAE"]
    print(f"\nLinearRegression MAE improvement vs baseline: {improvement_lr:.3f}")
    improvement_rf = baseline_results["MAE"] - rf_results["MAE"]
    print(f"RandomForestRegressor MAE improvement vs baseline: {improvement_rf:.3f}")

    version_metadata = {
        "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "best_model_name": best_model_name,
        "model_type": type(best_model).__name__,
        "feature_cols": FEATURE_COLS,
        "training_data_source": {
            **dataset_metadata,
            "rows_after_dropna": len(df),
        },
        "train_test_split": {
            "method": "season-aware rolling GW split",
            "split_ratio": split_ratio,
            "train_rows": len(train_df),
            "test_rows": len(test_df),
            "season_summaries": split_summary,
        },
        "split_order_check": split_validation,
        "training_config": {
            "target_column": TARGET_COL,
            "train_split_ratio": TRAIN_SPLIT_RATIO,
            "train_random_seed": TRAIN_RANDOM_SEED,
            "rf_n_estimators": RF_N_ESTIMATORS,
            "rf_max_depth": RF_MAX_DEPTH,
            "rf_min_samples_leaf": RF_MIN_SAMPLES_LEAF,
            "baseline_strategy": BASELINE_STRATEGY,
        },
        "metrics": {
            "lr": {"mae": lr_results["MAE"], "rmse": lr_results["RMSE"]},
            "rf": {"mae": rf_results["MAE"], "rmse": rf_results["RMSE"]},
            "baseline": {"mae": baseline_results["MAE"], "rmse": baseline_results["RMSE"]},
        },
    }
    write_json_atomic(version_dir / "metadata.json", version_metadata)

    latest_metadata = {
        "version": version,
        "created_at": version_metadata["created_at"],
        "model_dir": f"models/{version}",
        "model_path": f"models/{version}/production_model.joblib",
        "scaler_path": f"models/{version}/scaler.joblib",
        "metadata_path": f"models/{version}/metadata.json",
        "best_model_name": best_model_name,
        "model_type": type(best_model).__name__,
        "mae": models[best_model_name]["MAE"],
        "rmse": models[best_model_name]["RMSE"],
    }
    write_json_atomic(LATEST_METADATA_PATH, latest_metadata)
    print(f"Saved version: {version}")

    if logs:
        print("\n===== LinearRegression Weights =====")
        print("Intercept/bias:", lr.intercept_)

        for feature_name, weight in zip(FEATURE_COLS, lr.coef_):
            print(f"{feature_name:<22}: {weight:.4f}")

        print("\n===== Sample Predictions =====")

        print("\nLinearRegression:")
        for i in range(min(10, len(y_test))):
            print(f"{y_test.iloc[i]:>5.0f} -> {lr_results['y_pred'][i]:>6.2f}")

        print("\nRandomForestRegressor:")
        for i in range(min(10, len(y_test))):
            print(f"{y_test.iloc[i]:>5.0f} -> {rf_results['y_pred'][i]:>6.2f}")

        print("\nMeanBaseline:")
        for i in range(min(10, len(y_test))):
            print(f"{y_test.iloc[i]:>5.0f} -> {baseline_results['y_pred'][i]:>6.2f}")


if __name__ == "__main__":
    main(logs=True)
