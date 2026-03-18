#download_players.py
import time
from S1.data_utils import download_json
from shared.db.connection import engine
import pandas as pd

BASE_URL = "https://fantasy.premierleague.com/api/element-summary/{id}/"


def load_player_ids() -> list[int]:
    df = pd.read_sql("SELECT id FROM raw.players ORDER BY id", engine)
    return df["id"].tolist()


def fetch_player_summary(player_id: int) -> dict:
    url = BASE_URL.format(id=player_id)
    return download_json(url)

def save_history(rows: list):
    df = pd.DataFrame(rows)

    df["kickoff_time"] = pd.to_datetime(df["kickoff_time"], utc=True)

    df.to_sql(
        "player_history",
        engine,
        schema="raw",
        if_exists="append",
        index=False
    )

def main(sleep_seconds: float = 0.0000000000000003):
    player_ids = load_player_ids()

    rows = []

    for i, pid in enumerate(player_ids, start=1):
        try:
            data = fetch_player_summary(pid)

            for h in data.get("history", []):
                rows.append({
                    "player_id": pid,
                    "fixture": h.get("fixture"),
                    "round": h.get("round"),
                    "kickoff_time": h.get("kickoff_time"),
                    "opponent_team": h.get("opponent_team"),
                    "was_home": h.get("was_home"),
                    "minutes": h.get("minutes"),
                    "total_points": h.get("total_points"),
                    "goals_scored": h.get("goals_scored"),
                    "assists": h.get("assists"),
                    "clean_sheets": h.get("clean_sheets"),
                    "goals_conceded": h.get("goals_conceded"),
                    "saves": h.get("saves"),
                    "bonus": h.get("bonus"),
                    "bps": h.get("bps"),
                    "expected_goals": h.get("expected_goals"),
                    "expected_assists": h.get("expected_assists"),
                    "expected_goals_conceded": h.get("expected_goals_conceded"),
                    "value": h.get("value"),
                })

            print(f"[{i}/{len(player_ids)}] OK player_id={pid}")

        except Exception as e:
            print(f"[{i}/{len(player_ids)}] FAIL player_id={pid}: {e}")

        time.sleep(sleep_seconds)

    save_history(rows)

    print(f"\nSaved {len(rows)} player history rows to database.")


if __name__ == "__main__":
    main()
