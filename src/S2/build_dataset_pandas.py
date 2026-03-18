#build_dataset_pandas.py
# Build dataset for the current season, using the raw JSON files downloaded from the FPL API.
from pathlib import Path
import pandas as pd
from shared.db.connection import engine


BOOTSTRAP_PATH = Path("data/raw/bootstrap-static.json")
OUT_PATH = Path("data/processed/current_season_raw.csv")

SEASON = "25-26"


def build_current_season(out_path: Path):
    query = """
    SELECT
        ph.player_id,
        ph.round AS "GW",
        ph.minutes,
        ph.total_points,
        ph.clean_sheets,
        ph.bps,
        ph.saves,
        ph.expected_goals,
        ph.expected_assists,
        ph.expected_goals_conceded,
        ph.value,
        ph.was_home,
        ph.opponent_team,
        ph.fixture,

        CONCAT(p.first_name, ' ', p.second_name) AS name,
        CASE
            WHEN p.element_type = 1 THEN 'GKP'
            WHEN p.element_type = 2 THEN 'DEF'
            WHEN p.element_type = 3 THEN 'MID'
            WHEN p.element_type = 4 THEN 'FWD'
        END AS position
    FROM raw.player_history ph
    JOIN raw.players p
        ON ph.player_id = p.id
    ORDER BY ph.player_id, ph.round, ph.fixture
    """

    df = pd.read_sql(query, engine)

    df["season"] = SEASON

    # ---- Tipuskonverzio ----
    numeric_cols = [
        "GW", "minutes", "total_points",
       # "goals_scored", "assists", 
        "clean_sheets",
       # "goals_conceded", "bonus", 
        "bps",
        "saves",
        #"influence", "creativity", "threat",
        #"ict_index", 
        "expected_goals",
        "expected_assists",
       # "expected_goal_involvements",
        "expected_goals_conceded",
        "value",
        "opponent_team",
        "fixture",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values(["player_id", "GW", "fixture"])

    final_cols = [
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
        "was_home",
        "opponent_team",
        "fixture",
    ]

    df = df[final_cols]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"OK: wrote {len(df)} rows to {out_path}")

def main():
        build_current_season(OUT_PATH)

if __name__ == "__main__":
    main()