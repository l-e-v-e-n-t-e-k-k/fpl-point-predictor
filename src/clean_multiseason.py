import pandas as pd
from pathlib import Path

INPUT = Path("data/processed/multiseason_supervised.csv")
OUTPUT = Path("data/processed/multiseason_clean.csv")


df = pd.read_csv(INPUT)

# -----------------------------------
# Csak a szukseges oszlopok
# -----------------------------------

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

df.to_csv(OUTPUT, index=False)

print("Rows after cleaning:", len(df))
print("Seasons:", df["season"].unique())

