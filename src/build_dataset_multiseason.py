#build_dataset_multiseason.py
# Build a dataset for multiple seasons, by merging the previous seasons' CSVs with the current season's CSV.
import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("data/raw/prev_seasons")
PROCESSED_DIR = Path("data/processed")

OUT_PATH = PROCESSED_DIR / "multiseason_supervised.csv"


def process_prev_season(merged_path, fixtures_path, season_name):

    df = pd.read_csv(merged_path)
    fixtures_df = pd.read_csv(fixtures_path)

    # Difficulty merge
    df = df.merge(
        fixtures_df[["id", "team_h_difficulty", "team_a_difficulty"]],
        left_on="fixture",
        right_on="id",
        how="left"
    )

    df["team_difficulty"] = np.where(
        df["was_home"] == True,
        df["team_h_difficulty"],
        df["team_a_difficulty"]
    )

    df["opponent_difficulty"] = np.where(
        df["was_home"] == True,
        df["team_a_difficulty"],
        df["team_h_difficulty"]
    )

    df["season"] = season_name

    df = df.drop(columns=["id", "team_h_difficulty", "team_a_difficulty"])

    # TARGET
    df = df.sort_values(["season", "name", "GW"])

    df["target_next_gw"] = (
    df.groupby(["season", "name"])["total_points"]
      .shift(-1)
    )

    df = df.dropna(subset=["target_next_gw"])

    keep_cols = [
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
        "team_difficulty", # az adott csapatnak mennyire nehez a meccs
        "opponent_difficulty", # az ellenfelnek mennyire nehez a meccs/ azaz az adott csapat mennyire jo
        "target_next_gw"
    ]
        # "team_h_difficulty" = otthoni csapatnak mennyire nehez
        # "team_a_difficulty" = vendeg csapatnak mennyire nehez
    df = df[keep_cols]


    # -----------------------------------
    #  0 perces sorok kidobása
    # -----------------------------------

    df = df[df["minutes"] > 0]

    # -----------------------------------
    # akik az utolso szezonban aktivak
    # -----------------------------------

    df = df.groupby("name").filter(lambda x: x["minutes"].sum() >= 300)

    # -----------------------------------
    #  Biztonsagi NaN drop
    # -----------------------------------

    df = df.dropna()

    return df


def main():

    all_dfs = []

    seasons = [
        ("merged_gw_22-23.csv", "fixtures_22-23.csv", "22-23"),
        ("merged_gw_23-24.csv", "fixtures_23-24.csv", "23-24"),
        ("merged_gw_24-25.csv", "fixtures_24-25.csv", "24-25"),
    ]

    for merged_file, fixtures_file, season_name in seasons:

        print("Processing:", season_name)

        merged_path = RAW_DIR / merged_file
        fixtures_path = RAW_DIR / fixtures_file

        df_season = process_prev_season(
            merged_path,
            fixtures_path,
            season_name
        )

        all_dfs.append(df_season)

    # CURRENT SEASON
    current_df = pd.read_csv(PROCESSED_DIR / "current_season_supervised.csv")
  #  current_df["season"] = "25-26"

    all_dfs.append(current_df)

    final_df = pd.concat(all_dfs, ignore_index=True)

    final_df.to_csv(OUT_PATH, index=False)

    print("DONE")
    print("Total rows:", len(final_df))


if __name__ == "__main__":
    main()