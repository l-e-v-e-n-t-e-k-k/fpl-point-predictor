import json
from pathlib import Path
import pandas as pd
import numpy as np

RAW_PATH = Path("data/processed/current_season_raw.csv")
FIXTURES_PATH = Path("data/raw/fixtures.json")
OUT_PATH = Path("data/processed/current_season_with_difficulty.csv")


def main():

    df = pd.read_csv(RAW_PATH)

    fixtures_json = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    fixtures_df = pd.DataFrame(fixtures_json)

    fixtures_df = fixtures_df[[
        "id",
        "team_h_difficulty",
        "team_a_difficulty"
    ]]

    df = df.merge(
        fixtures_df,
        left_on="fixture",
        right_on="id",
        how="left"
    )

    # Own team difficulty
    df["team_difficulty"] = np.where(
        df["was_home"] == True,
        df["team_h_difficulty"],
        df["team_a_difficulty"]
    )

    # Opponent difficulty
    df["opponent_difficulty"] = np.where(
        df["was_home"] == True,
        df["team_a_difficulty"],
        df["team_h_difficulty"]
    )

    df = df.drop(columns=["id", "team_h_difficulty", "team_a_difficulty", "fixture", "opponent_team"])

    df.to_csv(OUT_PATH, index=False)

    print("OK: difficulty merged")


if __name__ == "__main__":
    main()