import csv
import json
from pathlib import Path

PLAYERS_DIR = Path("data/raw/players")
OUT_PATH = Path("data/processed/match_history.csv")


def safe_get(d: dict, key: str, default=None):
    v = d.get(key, default)
    return default if v is None else v


def build_match_history(players_dir: Path, out_path: Path):
    if not players_dir.exists():
        raise FileNotFoundError(
            f"Not found: {players_dir}. Elobb: python3 src/download_players.py"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Ha valamelyik hianyzik, uresen marad (default).
    fields = [
        "player_id",
        "gw",
        "minutes",
        "total_points",
        "goals_scored",
        "assists",
        "clean_sheets",
        "goals_conceded",
        "yellow_cards",
        "red_cards",
        "saves",
        "bonus",
        "bps",
        "ict_index",
        "influence",
        "creativity",
        "threat",
        "expected_goals",
        "expected_assists",
        "expected_goal_involvements",
        "expected_goals_conceded",
        "value",
        "was_home",
        "opponent_team",
    ]

    player_files = sorted(players_dir.glob("*.json"))
    if not player_files:
        raise FileNotFoundError(f"Nincs egyetlen JSON sem itt: {players_dir}")

    rows = 0

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for pf in player_files:
            player_id = int(pf.stem)
            data = json.loads(pf.read_text(encoding="utf-8"))

            history = data.get("history", [])
            # history: list of game-by-game stats
            for h in history:
                row = {
                    "player_id": player_id,
                    "gw": safe_get(h, "round"),
                    "minutes": safe_get(h, "minutes"),
                    "total_points": safe_get(h, "total_points"),
                    "goals_scored": safe_get(h, "goals_scored"),
                    "assists": safe_get(h, "assists"),
                    "clean_sheets": safe_get(h, "clean_sheets"),
                    "goals_conceded": safe_get(h, "goals_conceded"),
                    "yellow_cards": safe_get(h, "yellow_cards"),
                    "red_cards": safe_get(h, "red_cards"),
                    "saves": safe_get(h, "saves"),
                    "bonus": safe_get(h, "bonus"),
                    "bps": safe_get(h, "bps"),
                    "ict_index": safe_get(h, "ict_index"),
                    "influence": safe_get(h, "influence"),
                    "creativity": safe_get(h, "creativity"),
                    "threat": safe_get(h, "threat"),
                    "expected_goals": safe_get(h, "expected_goals"),
                    "expected_assists": safe_get(h, "expected_assists"),
                    "expected_goal_involvements": safe_get(h, "expected_goal_involvements"),
                    "expected_goals_conceded": safe_get(h, "expected_goals_conceded"),
                    "value": safe_get(h, "value"),
                    "was_home": safe_get(h, "was_home"),
                    "opponent_team": safe_get(h, "opponent_team"),
                }
                writer.writerow(row)
                rows += 1

    print(f"OK: wrote {rows} rows to {out_path}")


if __name__ == "__main__":
    build_match_history(PLAYERS_DIR, OUT_PATH)
