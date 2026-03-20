import joblib
import pandas as pd

from pathlib import Path
from fastapi import FastAPI
from shared.db.connection import engine
from S3.train_and_evaluate import FEATURE_COLS

app = FastAPI()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODEL_DIR / "production_model.joblib"
SCALER_PATH = MODEL_DIR / "scaler.joblib"

TOP_K = 20

model = None
scaler = None
player_meta = {}


# ---- helper functions ----
def normalize_name(name: str) -> str:
    if not name:
        return ""
    return " ".join(name.lower().strip().split())


def pos_name(element_type: int) -> str:
    return {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}.get(element_type, str(element_type))


def load_player_meta() -> dict:
    meta_df = pd.read_sql(
        """
        SELECT
            p.first_name,
            p.second_name,
            p.web_name,
            p.element_type,
            p.now_cost,
            t.name AS team_name
        FROM raw.players p
        LEFT JOIN raw.teams t
            ON p.team = t.id
        """,
        engine
    )

    meta = {}

    for row in meta_df.itertuples(index=False):
        full_name = f"{row.first_name} {row.second_name}".strip()
        key = normalize_name(full_name)

        meta[key] = {
            "name": full_name,
            "web_name": row.web_name,
            "team": row.team_name or "Unknown",
            "pos": pos_name(int(row.element_type)),
            "price": float(row.now_cost or 0) / 10.0,
        }

    return meta


# ---- startup ----
@app.on_event("startup")
def load_model():

    global model, scaler, player_meta

    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    player_meta = load_player_meta()

    print("Model loaded")


# ---- prediction endpoint ----
@app.get("/predict")
def predict():

    df = pd.read_sql("SELECT * FROM player_data", engine)

    query = """
    SELECT *
    FROM player_data
    WHERE season = (
        SELECT MAX(season) FROM player_data
    )
    AND GW = (
        SELECT MAX(GW)
        FROM player_data
        WHERE season = (
            SELECT MAX(season) FROM player_data
        )
    )
    """

    # df = pd.read_sql(query, engine)

    latest_season = df["season"].max()
    latest_gw = df[df["season"] == latest_season]["GW"].max()

    next_gw_df = df[
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

    # ---- top players ----
    top_results = []

    for i, row in enumerate(top_players.itertuples(), start=1):

        player_name = getattr(row, "name")

        meta = player_meta.get(
            normalize_name(player_name),
            {"team": "Unknown", "pos": "", "price": 0, "web_name": player_name}
        )

        top_results.append({
            "rank": i,
            "player": meta["web_name"],
            "team": meta["team"],
            "position": meta["pos"],
            "price": meta["price"],
            "predicted_points": float(row.predicted_points)
        })

    # ---- position results ----
    positions = ["GKP", "DEF", "MID", "FWD"]

    position_results = {}

    for pos in positions:

        pos_df = next_gw_df[next_gw_df["position"] == pos]

        top_pos = pos_df.sort_values(
            "predicted_points", ascending=False
        ).head(3)

        pos_list = []

        for i, row in enumerate(top_pos.itertuples(), start=1):

            player_name = getattr(row, "name")

            meta = player_meta.get(
                normalize_name(player_name),
                {"team": "Unknown", "pos": "", "price": 0, "web_name": player_name}
            )

            pos_list.append({
                "rank": i,
                "player": meta["web_name"],
                "team": meta["team"],
                "position": meta["pos"],
                "price": meta["price"],
                "predicted_points": float(row.predicted_points)
            })

        position_results[pos] = pos_list

    return {
        "gw": int(next_gw),
        "top_players": top_results,
        "top_by_position": position_results
    }
