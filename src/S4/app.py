import json
import joblib
import os
import pandas as pd

from pathlib import Path
from shared.http.json_client import fetch_url

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = Path(os.getenv("MODEL_BASE_DIR", str(PROJECT_ROOT / "models")))
LATEST_METADATA_PATH = MODEL_DIR / "latest.json"
S1_BASE_URL = os.getenv("S1_BASE_URL", "http://localhost:8002").strip()
S2_BASE_URL = os.getenv("S2_BASE_URL", "http://localhost:8001").strip()

TOP_K = 20

# ---- Helper functions ----
def normalize_name(name: str) -> str:
    if not name:
        return ""
    return " ".join(name.lower().strip().split())

def pos_name(element_type: int) -> str:
    return {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}.get(element_type, str(element_type))


def load_player_meta() -> dict:
    if not S1_BASE_URL:
        raise RuntimeError("S1_BASE_URL is required for app player metadata loading")

    payload = fetch_url(S1_BASE_URL, "player-meta")
    data = payload.get("data", [])
    meta_df = pd.DataFrame(data)

    player_meta = {}

    for row in meta_df.itertuples(index=False):
        full_name = f"{row.first_name} {row.second_name}".strip()
        key = normalize_name(full_name)

        player_meta[key] = {
            "name": full_name,
            "web_name": row.web_name,
            "team": row.team_name or "Unknown",
            "pos": pos_name(int(row.element_type)),
            "price": float(row.now_cost or 0) / 10.0,
        }

    return player_meta


def resolve_path(path_str: str):
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_latest_paths():
    with LATEST_METADATA_PATH.open("r", encoding="utf-8") as f:
        latest = json.load(f)

    model_path = resolve_path(latest["model_path"])
    scaler_path = resolve_path(latest["scaler_path"])
    metadata_path = resolve_path(latest["metadata_path"])
    return model_path, scaler_path, metadata_path, latest


def predict():

    model_path, scaler_path, metadata_path, latest = load_latest_paths()
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    with metadata_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)
    feature_cols = metadata["feature_cols"]
    
    print(f"Loaded production model: {latest['version']} ({latest['model_type']})")

    # ---- Load metadata ----
    player_meta = load_player_meta()

    # ---- Load match history ----
    if not S2_BASE_URL:
        raise RuntimeError("S2_BASE_URL is required for app prediction loading")

    payload = fetch_url(S2_BASE_URL, "/player-data/latest")
    data = payload.get("data", [])
    df = pd.DataFrame(data)
    ## ---- Add features and predict next GW ----

    latest_season = df["season"].max()
    latest_gw = df[df["season"] == latest_season]["GW"].max()

    next_gw_df = df[                        # last season last GW players data
        (df["season"] == latest_season) &
        (df["GW"] == latest_gw)
    ].copy()

    X_next = next_gw_df[feature_cols]

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
 
