# src/train_and_evaluate.py

import csv
from pathlib import Path

from features import build_supervised
from model import fit_linear_regression, predict_batch

IN_PATH = Path("data/processed/match_history.csv")


# ---------- 1) CSV beolvasas ----------
def load_rows(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)

        for row in r:
            # fontos mezok
            row["player_id"] = int(row["player_id"])
            row["gw"] = int(row["gw"]) if row["gw"] not in (None, "", "None") else None
            row["minutes"] = float(row["minutes"]) if row["minutes"] not in (None, "", "None") else 0.0
            row["total_points"] = float(row["total_points"]) if row["total_points"] not in (None, "", "None") else 0.0
            rows.append(row)

    return rows

# ---------- 2) Idosoros split (egyszeru) + ertekeles ----------
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

def mae(y_true, y_pred):
    return sum(abs(a - b) for a, b in zip(y_true, y_pred)) / max(1, len(y_true))

def rmse(y_true, y_pred):
    return (sum((a - b) ** 2 for a, b in zip(y_true, y_pred)) / max(1, len(y_true))) ** 0.5


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

    w = fit_linear_regression(X_train, y_train)
    y_pred = predict_batch(X_test, w)

    print("\nWeights (bias + 4 feature):")
    print(w)

    print("\nMetrics:")
    print(f"MAE : {mae(y_test, y_pred):.3f}")
    print(f"RMSE: {rmse(y_test, y_pred):.3f}")


    print("\nSample predictions (true -> pred):")
    for i in range(min(10, len(y_test))):
        print(f"{y_test[i]:.0f} -> {y_pred[i]:.2f}")


if __name__ == "__main__":
    main()
