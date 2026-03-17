#build_dataset_multiseason.py
# Build a dataset for multiple seasons, by merging the previous seasons' CSVs with the current season's CSV.
import pandas as pd
import numpy as np
from features import add_rolling_features
from pathlib import Path
from shared.db.connection import engine

RAW_DIR = Path("data/raw/prev_seasons")
PROCESSED_DIR = Path("data/processed")

OUT_PATH = PROCESSED_DIR / "multiseason_supervised.csv"

KEEP_COLS = [
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
        "is_home",
        "target_next_gw"
]
        # "team_h_difficulty" = otthoni csapatnak mennyire nehez
        # "team_a_difficulty" = vendeg csapatnak mennyire nehez

def process_prev_season(merged_path, fixtures_path, season_name):

    df = pd.read_csv(merged_path)
    fixtures_df = pd.read_csv(fixtures_path)

    # ---- Difficulty merge ----
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

    df = df.sort_values(["season", "name", "GW"])

    df["target_next_gw"] = (
    df.groupby(["season", "name"])["total_points"]
      .shift(-1)
    )

    df["is_home"] = (df["was_home"]).astype(int)

    df = df[KEEP_COLS]

    
    #  ---- Drop 0 minutes rows ----
    df = df[df["minutes"] > 0]

    # ---- Filter active players ----
    #df = df.groupby("name").filter(lambda x: x["minutes"].sum() >= 300)
    latest_season = df["season"].max()

    active_players = (
        df[df["season"] == latest_season]
        .groupby("name")["minutes"]
        .sum()
    )

    active_players = active_players[active_players >= 200].index

    df = df[df["name"].isin(active_players)]

    return df


def main():

    all_dfs = []

    seasons = [
        ("merged_gw_22-23.csv", "fixtures_22-23.csv", "22-23"),
        ("merged_gw_23-24.csv", "fixtures_23-24.csv", "23-24"),
        ("merged_gw_24-25.csv", "fixtures_24-25.csv", "24-25"),
    ]
    # ---- Merge previous seasons ----
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

    # ---- Merge with Current Season ----
    current_df = pd.read_csv(PROCESSED_DIR / "current_season_supervised.csv") # load current season

    current_df["is_home"] = (current_df["was_home"]).astype(int)

    current_df = current_df[KEEP_COLS]
    all_dfs.append(current_df)

    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df = add_rolling_features(final_df)
    final_df.to_csv(OUT_PATH, index=False)

    print("DONE")
    print("Total rows:", len(final_df))

    final_df.to_sql(
        "player_data",
        engine,
        if_exists="append",
        index=False
    )
    
if __name__ == "__main__":
    main()