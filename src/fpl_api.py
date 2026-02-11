import json
import time
from pathlib import Path
import urllib.request as urllib_request
import urllib.error as urllib_error

BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

def download_json(url: str, out_path: Path, ttl_hours: int = 12):
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists():
        age_seconds = time.time() - out_path.stat().st_mtime
        if age_seconds < ttl_hours * 3600:
            print("Using cached file.")
            return json.loads(out_path.read_text(encoding="utf-8"))

    print("Downloading fresh data...")
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

    data = json.loads(body.decode("utf-8"))
    out_path.write_text(json.dumps(data), encoding="utf-8")
    return data

def fetch_bootstrap_static():
    return download_json(
        BOOTSTRAP_URL,
        Path("data/raw/bootstrap-static.json")
    )

if __name__ == "__main__":
    data = fetch_bootstrap_static()
    print("Keys:", list(data.keys()))
    print("Players:", len(data["elements"]))
    print("Teams:", len(data["teams"]))
