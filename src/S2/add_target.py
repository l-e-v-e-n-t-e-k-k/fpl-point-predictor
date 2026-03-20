import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_PATH = PROCESSED_DIR / "current_season_with_difficulty.csv"
OUT_PATH = PROCESSED_DIR / "current_season_supervised.csv"


def add_target(df: pd.DataFrame):
    df = df.sort_values(["name", "GW", "fixture"])

    df["target_next_gw"] = (
        df.groupby("name")["total_points"]
        .shift(-1)
    )

    return df


def save_supervised(df: pd.DataFrame, out_path: Path = OUT_PATH):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print("OK: target column added")
    print("Final rows:", len(df))
    print(f"Saved to: {out_path}")


def main(in_path: Path = INPUT_PATH, out_path: Path = OUT_PATH):
    df = pd.read_csv(in_path)
    supervised_df = add_target(df)
    save_supervised(supervised_df, out_path)

if __name__ == "__main__":
    main()
