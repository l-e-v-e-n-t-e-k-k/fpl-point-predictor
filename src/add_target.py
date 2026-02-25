import pandas as pd
from pathlib import Path

INPUT_PATH = Path("data/processed/current_season_with_difficulty.csv")
OUT_PATH = Path("data/processed/current_season_supervised.csv")


def main():

    df = pd.read_csv(INPUT_PATH)

    df = df.sort_values(["player_id", "gw"])

    df["target_next_gw"] = (
        df.groupby("player_id")["total_points"]
        .shift(-1)
    )

    # Utolso GW sorok eldobasa
    df = df.dropna(subset=["target_next_gw"])

    df.to_csv(OUT_PATH, index=False)

    print("OK: target column added")
    print("Final rows:", len(df))


if __name__ == "__main__":
    main()