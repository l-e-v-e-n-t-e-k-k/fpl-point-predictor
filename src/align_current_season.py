import pandas as pd
import json
from pathlib import Path

CURRENT_PATH = Path("data/processed/current_season_supervised.csv")
BOOTSTRAP_PATH = Path("data/raw/bootstrap-static.json")
OUTPUT_PATH = Path("data/processed/current_season_aligned.csv")

# Load current season
df = pd.read_csv(CURRENT_PATH)

# Load bootstrap
bootstrap = json.loads(BOOTSTRAP_PATH.read_text(encoding="utf-8"))
elements = bootstrap["elements"]

meta = []
for e in elements:
    meta.append({
        "player_id": e["id"],
        "name": f"{e['first_name']} {e['second_name']}",
        "position": {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}[e["element_type"]]
    })

meta_df = pd.DataFrame(meta)

# Merge name + position
df = df.merge(meta_df, on="player_id", how="left")

df = df.rename(columns={"gw": "GW"})


df["season"] = "25-26"


keep_cols = [
    "season",
    "name",
    "position",
    "GW",
    "minutes",
    "total_points",
    "expected_goals",
    "expected_assists",
    "clean_sheets",
    "saves",
    "bps",
    "value",
    "team_difficulty",
    "opponent_difficulty",
    "target_next_gw"
]

df = df[keep_cols]

df.to_csv(OUTPUT_PATH, index=False)

print("Aligned current season rows:", len(df))