import pandas as pd
from pathlib import Path

MULTI_PATH = Path("data/processed/multiseason_clean.csv")
CURRENT_PATH = Path("data/processed/current_season_aligned.csv")
OUT_PATH = Path("data/processed/final_dataset.csv")

df_multi = pd.read_csv(MULTI_PATH)
df_current = pd.read_csv(CURRENT_PATH)

print("Multi columns:")
print(df_multi.columns.tolist())

print("\nCurrent columns:")
print(df_current.columns.tolist())

df_current = df_current[df_multi.columns]
# Aktiv jatekosok = akik current seasonben vannak
active_players = df_current["name"].unique()

# Szurjuk a regi szezonokat
df_multi = df_multi[df_multi["name"].isin(active_players)]


df_final = pd.concat([df_multi, df_current], ignore_index=True)

df_final = df_final.sort_values(["season", "name", "GW"])

df_final.to_csv(OUT_PATH, index=False)

print("\nFINAL DATASET INFO")
print("Rows:", len(df_final))
print("Seasons:", df_final["season"].unique())
print("Players:", df_final["name"].nunique())