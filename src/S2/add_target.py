import pandas as pd
from pathlib import Path

INPUT_PATH = Path("data/processed/current_season_with_difficulty.csv")
OUT_PATH = Path("data/processed/current_season_supervised.csv")


def add_target():

    df = pd.read_csv(INPUT_PATH)

    df = df.sort_values(["name", "GW", "fixture"])

    df["target_next_gw"] = (
        df.groupby("name")["total_points"]
        .shift(-1)
    )

    df.to_csv(OUT_PATH, index=False)

    print("OK: target column added")
    print("Final rows:", len(df))

def main():
        add_target()

if __name__ == "__main__":
    main()
