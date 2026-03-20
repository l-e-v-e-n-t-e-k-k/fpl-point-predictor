import joblib
import pandas as pd

from pathlib import Path
from shared.db.connection import engine
from S3.train_and_evaluate import FEATURE_COLS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODEL_DIR / "production_model.joblib"
SCALER_PATH = MODEL_DIR / "scaler.joblib"

TOP_K = 20

# ---- Helper functions ----
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


def predict():

    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    
    print("Loaded production model:", type(model).__name__)

    # ---- Load metadata ----
    player_meta = load_player_meta()

    # ---- Load match history ----
    df = pd.read_sql(
        "SELECT * FROM player_data",
        engine
    )
    ## ---- Add features and predict next GW ----

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
 
