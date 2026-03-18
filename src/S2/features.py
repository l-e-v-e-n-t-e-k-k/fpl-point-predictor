import json
from pathlib import Path
import pandas as pd

MIN_AVG_MIN_LAST5 = 0.0
CURRENT_SEASON = "25-26"
CURRENT_SEASON_RAW_PATH = Path("data/processed/current_season_raw.csv")
FIXTURES_PATH = Path("data/raw/fixtures.json")


def fill_missing_next_difficulty(df: pd.DataFrame) -> pd.DataFrame:

    missing_mask = (
        df["season"].eq(CURRENT_SEASON)
        & (df["next_opponent_difficulty"].isna() | df["next_team_difficulty"].isna())
    )

    if not missing_mask.any() or not CURRENT_SEASON_RAW_PATH.exists() or not FIXTURES_PATH.exists():
        return df

    # ---- raw fixture mapping ----
    current_raw = pd.read_csv(CURRENT_SEASON_RAW_PATH)
    current_raw["is_home"] = current_raw["was_home"].astype(int)

    merge_keys = ["name", "GW", "minutes", "total_points", "value", "is_home"]

    fixture_lookup = (
        current_raw[merge_keys + ["fixture"]]
        .drop_duplicates(subset=merge_keys)
        .set_index(merge_keys)["fixture"]
    )

    # ---- fixtures table ----
    fixtures = pd.DataFrame(json.loads(FIXTURES_PATH.read_text(encoding="utf-8")))
    fixtures["kickoff_time"] = pd.to_datetime(fixtures["kickoff_time"], errors="coerce")

    fixtures = fixtures.sort_values(
        ["event", "kickoff_time", "id"], na_position="last"
    )

    # ---- next fixture difficulty by team ----
    next_fixture_by_team = {}

    for _, f in fixtures[~fixtures["finished"]].iterrows():

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

    fixture_rows = fixtures.set_index("id")

    # ---- fill missing values ----
    for idx in df.index[missing_mask]:

        row = df.loc[idx]

        key = tuple(row[col] for col in merge_keys)
        fixture_id = fixture_lookup.get(key)

        if pd.isna(fixture_id):
            continue

        fixture = fixture_rows.loc[fixture_id]

        team_id = fixture["team_h"] if row["is_home"] == 1 else fixture["team_a"]

        next_diff = next_fixture_by_team.get(team_id)

        if next_diff is None:
            continue

        next_team_diff, next_opp_diff = next_diff

        if pd.isna(df.at[idx, "next_team_difficulty"]):
            df.at[idx, "next_team_difficulty"] = next_team_diff

        if pd.isna(df.at[idx, "next_opponent_difficulty"]):
            df.at[idx, "next_opponent_difficulty"] = next_opp_diff

    return df


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Season-aware rolling feature engineering.

    Assumes df contains season, name, GW, total_points, minutes columns.

    Output:
        df with new rolling feature colums
    """
    
    df = df.sort_values(["season", "name", "GW"]).copy()

    ROLL_WINDOWS = [3, 5]

    for w in ROLL_WINDOWS:
        df[f"avg_pts_last{w}"] = (
            df.groupby(["season","name"])["total_points"]
            .shift(1)
            .rolling(w)
            .mean().round(3)
        )

        df[f"avg_min_last{w}"] = (
            df.groupby(["season","name"])["minutes"]
            .shift(1)
            .rolling(w)
            .mean().round(3)
        )

    df["xgi"] = df["expected_goals"] + df["expected_assists"]

    df["avg_xgi_last5"] = (
        df.groupby(["season","name"])["xgi"]
        .shift(1)
        .rolling(5)
        .mean().round(3)
    )

    df["xgi"] = df["xgi"].round(3)

    df["next_opponent_difficulty"] = (
        df.groupby(["season", "name"])["opponent_difficulty"]
        .shift(-1).round(0)
    )
    df["next_team_difficulty"] = (
        df.groupby(["season", "name"])["team_difficulty"]
        .shift(-1).round(0)
    )

    df = fill_missing_next_difficulty(df)

    df["clean_sheets_last5"] = (
        df.groupby(["season","name"])["clean_sheets"]
        .shift(1)
        .rolling(5)
        .sum().round(0)
    )
    # --- Filter ---
    df = df[df["avg_pts_last5"].notna()]
   # df = df[df["avg_min_last5"] >= MIN_AVG_MIN_LAST5]

    return df
