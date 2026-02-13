import json
import time
from pathlib import Path
from data_utils import download_json

BOOTSTRAP_PATH = Path("data/raw/bootstrap-static.json")
PLAYERS_DIR = Path("data/raw/players")

BASE_URL = "https://fantasy.premierleague.com/api/element-summary/{id}/"


def load_bootstrap() -> dict:
    if not BOOTSTRAP_PATH.exists():
        raise FileNotFoundError(
            f"Nincs meg: {BOOTSTRAP_PATH}. Elotte: python3 src/fpl_api.py"
        )
    return json.loads(BOOTSTRAP_PATH.read_text(encoding="utf-8"))


def fetch_player_summary(player_id: int, ttl_hours: int = 24) -> dict:
    out_path = PLAYERS_DIR / f"{player_id}.json"
    url = BASE_URL.format(id=player_id)
    return download_json(url, out_path, ttl_hours=ttl_hours)


def main(n_players: int = 817, sleep_seconds: float = 0.3):
    data = load_bootstrap()
    player_ids = [p["id"] for p in data["elements"]]

    subset = player_ids[:n_players]

    ok = 0
    failed = 0

    for i, pid in enumerate(subset, start=1):
        try:
            fetch_player_summary(pid)
            ok += 1
            print(f"[{i}/{n_players}] OK  player_id={pid}")
        except Exception as e:
            failed += 1
            print(f"[{i}/{n_players}] FAIL player_id={pid} -> {type(e).__name__}: {e}")

        time.sleep(sleep_seconds)  # rate limit

    print(f"\nDone. OK={ok}, FAIL={failed}")
    print(f"Saved to: {PLAYERS_DIR.resolve()}")


if __name__ == "__main__":
    main()
