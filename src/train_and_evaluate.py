# src/train_and_evaluate.py
from pathlib import Path

from features import add_rolling_features

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

import joblib

import pandas as pd

IN_PATH = Path("data/processed/multiseason_supervised.csv")

FEATURE_COLS = [
    "avg_pts_last3",
    "avg_min_last3",
    "avg_pts_last5",
    "avg_min_last5",
    "expected_goals",
    "expected_assists",
    "expected_goals_conceded",
    "bps",
    "team_difficulty",
    "opponent_difficulty"
]

TARGET_COL = "target_next_gw"


# ---- Rolling GW split (season-aware) ----
def rolling_gw_split(df, split_ratio=0.7):
    """
    Minden szezonon belul:
        train: GW <= 70%
        test : GW > 70%
        - minden playernek van multja
    """

    train_parts = []
    test_parts = []

    for season, season_df in df.groupby("season"):

        max_gw = season_df["GW"].max()
        split_gw = int(max_gw * split_ratio)

        train_part = season_df[season_df["GW"] <= split_gw]
        test_part = season_df[season_df["GW"] > split_gw]

        train_parts.append(train_part)
        test_parts.append(test_part)

        print(f"{season}: max_gw={max_gw}, split_gw={split_gw}")

    train_df = pd.concat(train_parts)
    test_df = pd.concat(test_parts)

    return train_df, test_df


# ---- Metrics ----
def mae(y_true, y_pred):
    return sum(abs(a - b) for a, b in zip(y_true, y_pred)) / max(1, len(y_true))

def rmse(y_true, y_pred):
    return (sum((a - b) ** 2 for a, b in zip(y_true, y_pred)) / max(1, len(y_true))) ** 0.5
 
# ---- Evaluation helper ----
def evaluate_model(model, X_train, y_train, X_test, y_test):

    model.fit(X_train, y_train)
    joblib.dump(model, "model.joblib")
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

def main():

    df = pd.read_csv(IN_PATH)

    df = add_rolling_features(df)

    #df_model = df.dropna(subset=["avg_pts_last5"])
    #df_model = df_model[df_model["avg_min_last5"] >= 0.0]

    train_df, test_df = rolling_gw_split(df, split_ratio=0.7)

    X_train = train_df[FEATURE_COLS]   # .values.tolist() numpy array -> list of lists
    y_train = train_df[TARGET_COL]
    
    X_test = test_df[FEATURE_COLS]
    y_test = test_df[TARGET_COL]

    # --- Feature Scaling ---
    scaler = StandardScaler()
    scaler.fit(X_train)
    
    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)    

   # X_train = [[1.0] + row for row in X_train]
   # X_test = [[1.0] + row for row in X_test]

    print("Train rows:", len(train_df))
    print("Test rows :", len(test_df))

    if len(y_train) < 20 or len(y_test) < 10:
        print("Tul keves adat.")
        return

    # ---- Linear Regression ----
    lr = LinearRegression()
    lr_results = evaluate_model(lr, X_train_scaled, y_train, X_test_scaled, y_test)

    # ---- Random Forest Regressor ----
    rf = RandomForestRegressor(n_estimators=300, random_state=42, max_depth=10, min_samples_leaf=5)
    rf_results = evaluate_model(rf, X_train, y_train, X_test, y_test)

    # ---- Mean Baseline ----
    baseline = DummyRegressor(strategy="mean")
    baseline_results = evaluate_model(baseline, X_train, y_train, X_test, y_test)

    # ---- Save models ----
    MODEL_DIR = Path("models")
    MODEL_DIR.mkdir(exist_ok=True)

    joblib.dump(lr, MODEL_DIR / "linear_regression.joblib")
    joblib.dump(rf, MODEL_DIR / "random_forest.joblib")
    joblib.dump(baseline, MODEL_DIR / "baseline.joblib")

    joblib.dump(scaler, MODEL_DIR / "scaler.joblib")
        
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
    
    joblib.dump(best_model, MODEL_DIR / "production_model.joblib")
    print(
        f"\nBest model: {best_model_name} "
        f"with MAE: {models[best_model_name]['MAE']:.3f}"
    )

    # ---- Print comparison ----
    print("\n===== Model Comparison =====")

    print("\n===== LinearRegression Weights =====")

    print("Intercept (bias):", lr.intercept_)

    for feature_name, weight in zip(FEATURE_COLS, lr.coef_):
        print(f"{feature_name:<22}: {weight:.4f}")

    print(f"LinearRegression  -> MAE: {lr_results['MAE']:.3f}, RMSE: {lr_results['RMSE']:.3f}")
    print(f"RandomForestRegressor -> MAE: {rf_results['MAE']:.3f}, RMSE: {rf_results['RMSE']:.3f}")
    print(f"MeanBaseline      -> MAE: {baseline_results['MAE']:.3f}, RMSE: {baseline_results['RMSE']:.3f}")

    improvement = baseline_results["MAE"] - lr_results["MAE"]
    print(f"\nMAE improvement vs baseline: {improvement:.3f}")

    # ---- Sample predictions ----
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
    main()
