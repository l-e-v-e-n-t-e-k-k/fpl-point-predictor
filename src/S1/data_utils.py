# src/data_utils.py
import json
import time
from pathlib import Path
import urllib.request as urllib_request
import urllib.error as urllib_error


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
