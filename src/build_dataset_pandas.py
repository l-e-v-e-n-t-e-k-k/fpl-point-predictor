import json
from pathlib import Path
import pandas as pd

PLAYERS_DIR = Path("data/raw/players")
OUT_PATH = Path("data/processed/current_season_raw.csv")


def build_current_season(players_dir: Path, out_path: Path):

    rows = []

    player_files = sorted(players_dir.glob("*.json"))

    for pf in player_files:
        player_id = int(pf.stem)
        data = json.loads(pf.read_text(encoding="utf-8"))

        history = data.get("history", [])

        for h in history:
            rows.append({
                "player_id": player_id,
                "gw": h.get("round"),
                "minutes": h.get("minutes"),
                "total_points": h.get("total_points"),
                "goals_scored": h.get("goals_scored"),
                "assists": h.get("assists"),
                "clean_sheets": h.get("clean_sheets"),
                "goals_conceded": h.get("goals_conceded"),
                "bonus": h.get("bonus"),
                "bps": h.get("bps"),
                "saves": h.get("saves"), 
                "influence": h.get("influence"),
                "creativity": h.get("creativity"),
                "threat": h.get("threat"),
                "ict_index": h.get("ict_index"),
                "expected_goals": h.get("expected_goals"),
                "expected_assists": h.get("expected_assists"),
                "expected_goal_involvements": h.get("expected_goal_involvements"),
                "expected_goals_conceded": h.get("expected_goals_conceded"),
                "value": h.get("value"),
                "was_home": h.get("was_home"),
                "opponent_team": h.get("opponent_team"),
                "fixture": h.get("fixture"),
            })

    df = pd.DataFrame(rows)

    # ---- Típuskonverzió ----
    numeric_cols = [
        "gw", "minutes", "total_points",
        "goals_scored", "assists", "clean_sheets",
        "goals_conceded", "bonus", "bps",
        "saves",
        "influence", "creativity", "threat",
        "ict_index", "expected_goals",
        "expected_assists",
        "expected_goal_involvements",
        "expected_goals_conceded",
        "value"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values(["player_id", "gw"])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"OK: wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    build_current_season(PLAYERS_DIR, OUT_PATH)