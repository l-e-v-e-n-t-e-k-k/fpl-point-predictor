import json
import time
from pathlib import Path
import urllib.request as urllib_request
import urllib.error as urllib_error

BOOTSTRAP_PATH = Path("data/raw/bootstrap-static.json")
PLAYERS_DIR = Path("data/raw/players")

BASE_URL = "https://fantasy.premierleague.com/api/element-summary/{id}/"


def load_bootstrap() -> dict:
    if not BOOTSTRAP_PATH.exists():
        raise FileNotFoundError(
            f"Nem találom: {BOOTSTRAP_PATH}. Előbb futtasd: python3 src/fpl_api.py"
        )
    return json.loads(BOOTSTRAP_PATH.read_text(encoding="utf-8"))


def download_json(url: str, out_path: Path, ttl_hours: int = 24) -> dict:
    """
    Letölt egy JSON-t és elmenti fájlba.
    Cache: ha a fájl frissebb, mint ttl_hours, akkor nem tölt újra.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists():
        age_seconds = time.time() - out_path.stat().st_mtime
        if age_seconds < ttl_hours * 3600:
            return json.loads(out_path.read_text(encoding="utf-8"))

    req = urllib_request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urllib_request.urlopen(req, timeout=30) as resp:
            body = resp.read()
    except urllib_error.HTTPError:
        raise
    except urllib_error.URLError:
        raise

    data = json.loads(body.decode("utf-8"))
    out_path.write_text(json.dumps(data), encoding="utf-8")
    return data


def fetch_player_summary(player_id: int, ttl_hours: int = 24) -> dict:
    out_path = PLAYERS_DIR / f"{player_id}.json"
    url = BASE_URL.format(id=player_id)
    return download_json(url, out_path, ttl_hours=ttl_hours)


def main(n_players: int = 50, sleep_seconds: float = 0.35):
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
