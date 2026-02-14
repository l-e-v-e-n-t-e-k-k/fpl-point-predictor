# src/train_and_evaluate.py

import csv
from pathlib import Path

from data_utils import load_rows
from features import build_supervised
from model import LinearRegression, MeanBaseline

IN_PATH = Path("data/processed/match_history.csv")


# ---------- Idosoros split ----------
def train_test_split_time(rows, split_gw: int):
    """
    A match_history sorokból csak a split_gw alapján vágunk:
    - train: gw <= split_gw
    - test:  gw >  split_gw
    A supervised datasetet mindkettőn külön építjük.
    """
    train_rows = [r for r in rows if r["gw"] <= split_gw]
    test_rows = [r for r in rows if r["gw"] > split_gw]
    return train_rows, test_rows

# ---------- Metrics ----------
def mae(y_true, y_pred):
    return sum(abs(a - b) for a, b in zip(y_true, y_pred)) / max(1, len(y_true))

def rmse(y_true, y_pred):
    return (sum((a - b) ** 2 for a, b in zip(y_true, y_pred)) / max(1, len(y_true))) ** 0.5
 
# ---------- Evaluation helper ----------
def evaluate_model(model, X_train, y_train, X_test, y_test):

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    return {
        "y_pred": y_pred,
        "MAE": mae(y_test, y_pred),
        "RMSE": rmse(y_test, y_pred)
    }

def main():
    rows = load_rows(IN_PATH)

    max_gw = max(r["gw"] for r in rows if r["gw"] is not None)
    split_gw = int(max_gw * 0.7)

    train_rows, test_rows = train_test_split_time(rows, split_gw)

    X_train, y_train = build_supervised(train_rows)
    X_test, y_test = build_supervised(test_rows)

    print(f"max_gw={max_gw}, split_gw={split_gw}")
    print(f"train examples={len(y_train)}, test examples={len(y_test)}")

    if len(y_train) < 20 or len(y_test) < 10:
        print("Tul keves adat.")
        return

   # w = fit_linear_regression(X_train, y_train)
   # y_pred = predict_batch(X_test, w)

        # ---- Linear Regression ----
    lr = LinearRegression()
    lr_results = evaluate_model(lr, X_train, y_train, X_test, y_test)

    # ---- Mean Baseline ----
    baseline = MeanBaseline()
    baseline_results = evaluate_model(baseline, X_train, y_train, X_test, y_test)

   # print("\nWeights (bias + 4 feature):")
   # print(w)

    print("\n===== Model Comparison =====")

    print("\n===== LinearRegression Weights =====")

    if lr.w is not None:
        print(f"Bias (intercept): {lr.w[0]:.4f}")
        print(f"avg_pts_last3   : {lr.w[1]:.4f}")
        print(f"avg_min_last3   : {lr.w[2]:.4f}")
        print(f"avg_pts_last5   : {lr.w[3]:.4f}")
        print(f"avg_min_last5   : {lr.w[4]:.4f}")   

    print(f"LinearRegression  -> MAE: {lr_results['MAE']:.3f}, RMSE: {lr_results['RMSE']:.3f}")
    print(f"MeanBaseline      -> MAE: {baseline_results['MAE']:.3f}, RMSE: {baseline_results['RMSE']:.3f}")

    improvement = baseline_results["MAE"] - lr_results["MAE"]
    print(f"\nMAE improvement vs baseline: {improvement:.3f}")

    # --------------------------------------------------
    # Sample predictions
    # --------------------------------------------------

    print("\n===== Sample Predictions =====")

    print("\nLinearRegression:")
    for i in range(min(10, len(y_test))):
        print(f"{y_test[i]:>5.0f} -> {lr_results['y_pred'][i]:>6.2f}")

    print("\nMeanBaseline:")
    for i in range(min(10, len(y_test))):
        print(f"{y_test[i]:>5.0f} -> {baseline_results['y_pred'][i]:>6.2f}")


if __name__ == "__main__":
    main()
