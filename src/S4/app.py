
import json
import joblib
import pandas as pd

from pathlib import Path
from db.connection import engine
from S3.train_and_evaluate import FEATURE_COLS

BOOTSTRAP_PATH = Path("data/raw/bootstrap-static.json")
# MATCH_HISTORY_PATH = Path("data/processed/multiseason_supervised.csv")

MODEL_PATH = Path("models/production_model.joblib")
SCALER_PATH = Path("models/scaler.joblib")

TOP_K = 20

# ---- Helper functions ----
def normalize_name(name: str) -> str:
    if not name:
        return ""
    return " ".join(name.lower().strip().split())

def pos_name(element_type: int) -> str:
    return {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}.get(element_type, str(element_type))


def predict():

    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    
    print("Loaded production model:", type(model).__name__)

    # ---- Load metadata ----
    # for printing team, position, price info in the output by matching player names
    bootstrap = json.loads(BOOTSTRAP_PATH.read_text(encoding="utf-8"))
    elements = bootstrap.get("elements", [])
    teams = {t["id"]: t["name"] for t in bootstrap.get("teams", [])}

    player_meta = {}
    for e in elements:
        first = e.get("first_name", "")
        second = e.get("second_name", "")
        web = e.get("web_name", "")

        full_name = f"{first} {second}".strip()

        key = normalize_name(full_name)

        player_meta[key] = {
            "name": full_name,
            "web_name": web,
            "team": teams.get(int(e.get("team", 0)), "Unknown"),
            "pos": pos_name(int(e.get("element_type", 0))),
            "price": float(e.get("now_cost", 0)) / 10.0,
        }

    # ---- Load match history ----
    #df = pd.read_csv(MATCH_HISTORY_PATH)
    df = pd.read_sql(
        "SELECT * FROM player_data",
        engine
    )
    ## ---- Add features and predict next GW ----
   # df = add_rolling_features(df)

    latest_season = df["season"].max()
    latest_gw = df[df["season"] == latest_season]["GW"].max()

    next_gw_df = df[                        # last season last GW players data
        (df["season"] == latest_season) &
        (df["GW"] == latest_gw)
    ].copy()

    X_next = next_gw_df[FEATURE_COLS]

    if "LinearRegression" in str(type(model)):
        X_next = scaler.transform(X_next)
    
    preds = model.predict(X_next)
    
    next_gw_df["predicted_points"] = preds

    top_players = next_gw_df.sort_values(
        "predicted_points", ascending=False
    ).head(TOP_K)

    next_gw = latest_gw + 1


    # ---- Print results ----
    print(f"\nPredicting GW {next_gw}")
    print("-" * 90)
    print(f"{'Rank':>4}  {'Player':<18}  {'Team':<18}  {'Pos':<3}  {'Price':>5}  {'PredPts':>7}")
    print("-" * 90)

    for i, row in enumerate(top_players.itertuples(), start=1):

        player_name = getattr(row, "name")

        meta = next(
            (p for p in player_meta.values() if p["name"] == player_name),
            {"team": "Unknown", "pos": "", "price": 0}
        )

        print(
            f"{i:>4}  "
            f"{meta['web_name']:<18.18}  "
            f"{meta['team']:<18.18}  "
            f"{meta['pos']:<3}  "
            f"{meta['price']:>5.1f}  "
            f"{row.predicted_points:>7.2f}"
        )

    print("-" * 90)

    positions = ["GKP", "DEF", "MID", "FWD"]

    for pos in positions:

        print(f"\nTop 3 {pos}")
        print("-" * 90)
        print(f"{'Rank':>4}  {'Player':<18}  {'Team':<18}  {'Pos':<3}  {'Price':>5}  {'PredPts':>7}")
        print("-" * 90)

        pos_df = next_gw_df[next_gw_df["position"] == pos]

        top_players = pos_df.sort_values(
            "predicted_points", ascending=False
        ).head(3)

        for i, row in enumerate(top_players.itertuples(), start=1):

            player_name = getattr(row, "name")

            meta = player_meta.get(
                normalize_name(player_name),
                {"team": "Unknown", "pos": "", "price": 0}
            )

            print(
                f"{i:>4}  "
                f"{meta['web_name']:<18.18}  "
                f"{meta['team']:<18.18}  "
                f"{meta['pos']:<3}  "
                f"{meta['price']:>5.1f}  "
                f"{row.predicted_points:>7.2f}"
            )

        print("-" * 90)

if __name__ == "__main__":
    predict()
 