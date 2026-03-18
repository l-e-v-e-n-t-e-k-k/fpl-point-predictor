from pathlib import Path
import pandas as pd
import numpy as np
from shared.db.connection import engine

RAW_PATH = Path("data/processed/current_season_raw.csv")
OUT_PATH = Path("data/processed/current_season_with_difficulty.csv")


def main():

    df = pd.read_csv(RAW_PATH)

    fixtures_df = pd.read_sql(
        """
        SELECT
            id,
            event,
            kickoff_time,
            team_h,
            team_a,
            team_h_difficulty,
            team_a_difficulty,
            finished
        FROM raw.fixtures
        """,
        engine
    )

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

        team_id = row["team_h"] if row["was_home"] else row["team_a"]
        next_diff = next_fixture_by_team.get(team_id)

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
            "team_h",
            "team_a",
            "team_h_difficulty",
            "team_a_difficulty",
            "finished",
            "opponent_team",
        ]
    )

    df.to_csv(OUT_PATH, index=False)

    print("OK: difficulty merged")


if __name__ == "__main__":
    main()
