import os
from pathlib import Path

import pandas as pd
import numpy as np

from shared.http.json_client import fetch_url

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RAW_PATH = PROCESSED_DIR / "current_season_raw.csv"
OUT_PATH = PROCESSED_DIR / "current_season_with_difficulty.csv"
S1_BASE_URL = os.getenv("S1_BASE_URL", "http://localhost:8002").strip()


def load_fixtures_df():
    if not S1_BASE_URL:
        raise RuntimeError("S1_BASE_URL is required for S2 fixture loading")

    payload = fetch_url(S1_BASE_URL, "fixtures")
    data = payload.get("data", [])
    return pd.DataFrame(data)


def merge_difficulty(df: pd.DataFrame):
    fixtures_df = load_fixtures_df()

    df = df.merge(
        fixtures_df,
        left_on="fixture",
        right_on="id",
        how="left",
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

    df = df.sort_values(["name", "GW", "fixture"])

    df["next_team_difficulty"] = (
        df.groupby("name")["team_difficulty"]
        .shift(-1)
    )

    df["next_opponent_difficulty"] = (
        df.groupby("name")["opponent_difficulty"]
        .shift(-1)
    )

    upcoming_fixtures = fixtures_df[~fixtures_df["finished"]].copy()
    upcoming_fixtures["kickoff_time"] = pd.to_datetime(
        upcoming_fixtures["kickoff_time"], errors="coerce"
    )
    upcoming_fixtures = upcoming_fixtures.sort_values(
        ["event", "kickoff_time", "id"], na_position="last"
    )

    next_fixture_by_team = {}

    for _, f in upcoming_fixtures.iterrows():
        if f["team_h"] not in next_fixture_by_team:
            next_fixture_by_team[f["team_h"]] = (
                f["team_h_difficulty"],
                f["team_a_difficulty"],
            )

        if f["team_a"] not in next_fixture_by_team:
            next_fixture_by_team[f["team_a"]] = (
                f["team_a_difficulty"],
                f["team_h_difficulty"],
            )

    missing_mask = (
        df["next_team_difficulty"].isna()
        | df["next_opponent_difficulty"].isna()
    )

    for idx in df.index[missing_mask]:
        row = df.loc[idx]

        next_diff = next_fixture_by_team.get(row["team_id"])

        if next_diff is None:
            continue

        next_team_diff, next_opp_diff = next_diff

        if pd.isna(df.at[idx, "next_team_difficulty"]):
            df.at[idx, "next_team_difficulty"] = next_team_diff

        if pd.isna(df.at[idx, "next_opponent_difficulty"]):
            df.at[idx, "next_opponent_difficulty"] = next_opp_diff

    df = df.drop(
        columns=[
            "id",
            "event",
            "kickoff_time",
            "team_h_difficulty",
            "team_a_difficulty",
            "finished",
            "opponent_team",
        ],
        errors="ignore",
    )

    return df


def save_with_difficulty(df: pd.DataFrame, out_path: Path = OUT_PATH):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"OK: difficulty merged -> {out_path}")


def main(in_path: Path = RAW_PATH, out_path: Path = OUT_PATH):
    df = pd.read_csv(in_path)
    merged_df = merge_difficulty(df)
    save_with_difficulty(merged_df, out_path)

if __name__ == "__main__":
    main()
