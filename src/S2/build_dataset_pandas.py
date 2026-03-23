#build_dataset_pandas.py
# Build dataset for the current season from the database.
import os
from pathlib import Path

import numpy as np
import pandas as pd

from shared.http.json_client import fetch_url

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

OUT_PATH = PROCESSED_DIR / "current_season_raw.csv"

SEASON = "25-26"
S1_BASE_URL = os.getenv("S1_BASE_URL", "").strip()


def load_current_season_rows():
    if not S1_BASE_URL:
        raise RuntimeError("S1_BASE_URL is required for S2 current season loading")

    payload = fetch_url(S1_BASE_URL, "current-season")
    data = payload.get("data", [])
    return pd.DataFrame(data)


def build_current_season():
    df = pd.DataFrame(load_current_season_rows())

    df["season"] = SEASON

    # ---- Tipuskonverzio ----
    numeric_cols = [
        "GW", "minutes", "total_points",
       # "goals_scored", "assists", 
        "clean_sheets",
       # "goals_conceded", "bonus", 
        "bps",
        "saves",
        #"influence", "creativity", "threat",
        #"ict_index", 
        "expected_goals",
        "expected_assists",
       # "expected_goal_involvements",
        "expected_goals_conceded",
        "value",
        "opponent_team",
        "fixture",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["team_id"] = np.where(df["was_home"], df["team_h"], df["team_a"])
    df = df.sort_values(["player_id", "GW", "fixture"])

    final_cols = [
        "season",
        "name",
        "position",  
        "GW",
        "minutes",
        "total_points",
        "expected_goals",
        "expected_assists",
        "expected_goals_conceded",
        "clean_sheets",
        "saves",
        "bps",
        "value",
        "was_home",
        "team_id",
        "opponent_team",
        "fixture",
    ]

    df = df[final_cols]

    return df


def save_current_season(df: pd.DataFrame, out_path: Path = OUT_PATH) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"OK: wrote {len(df)} rows to {out_path}")

def main():
    df = build_current_season()
    save_current_season(df, OUT_PATH)

if __name__ == "__main__":
    main()
