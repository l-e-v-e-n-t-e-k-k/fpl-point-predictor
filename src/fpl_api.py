
from pathlib import Path
from data_utils import download_json

BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"


def fetch_bootstrap_static():
    return download_json(
        BOOTSTRAP_URL,
        Path("data/raw/bootstrap-static.json"),
        ttl_hours=12
    )

if __name__ == "__main__":
    data = fetch_bootstrap_static()
    print("Keys:", list(data.keys()))
    print("Players:", len(data["elements"]))
    print("Teams:", len(data["teams"]))
