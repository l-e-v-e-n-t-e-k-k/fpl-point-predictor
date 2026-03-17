#from pathlib import Path
import pandas as pd

MIN_AVG_MIN_LAST5 = 0.0


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
            df.groupby(["season", "name"])["total_points"]
            .transform(lambda x: x.shift(1).rolling(w).mean())
            .round(3)
        )

        df[f"avg_min_last{w}"] = (
            df.groupby(["season", "name"])["minutes"]
            .transform(lambda x: x.shift(1).rolling(w).mean())
            .round(3)
        )

    df["xgi"] = df["expected_goals"] + df["expected_assists"]

    df["avg_xgi_last5"] = (
        df.groupby(["season","name"])["xgi"]
        .transform(lambda x: x.shift(1).rolling(5).mean())
        .round(3)
    )

    df["xgi"] = df["xgi"].round(3)

    # --- Filter ---
    df = df[df["avg_pts_last5"].notna()]
   # df = df[df["avg_min_last5"] >= MIN_AVG_MIN_LAST5]

    return df
