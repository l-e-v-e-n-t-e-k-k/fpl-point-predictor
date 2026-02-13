# src/data_utils.py

import json
import time
from pathlib import Path
import csv
import urllib.request as urllib_request
import urllib.error as urllib_error


def load_rows(path: Path):
    """
    match_history.csv betoltese eegysegesen
    """

    rows = []

    with path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)

        for row in r:
            rows.append({
                "player_id": int(row["player_id"]),
                "gw": int(row["gw"]) if row["gw"] not in (None, "", "None") else None,
                "minutes": float(row["minutes"]) if row["minutes"] not in (None, "", "None") else 0.0,
                "total_points": float(row["total_points"]) if row["total_points"] not in (None, "", "None") else 0.0,
            })

    return rows

def download_json(url: str, out_path: Path, ttl_hours: int = 24) -> dict:
    """
    JSON letoltese es cache-elese TTL alapon
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
