#fpl_api.py
from pathlib import Path
from S1.data_utils import download_json

BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"


def fetch_bootstrap_static():
    return download_json(
        BOOTSTRAP_URL,
        Path("data/raw/bootstrap-static.json"),
        ttl_hours=12
    )

def fetch_fixtures():
    return download_json(
        FIXTURES_URL,
        Path("data/raw/fixtures.json"),
        ttl_hours=12
    )

def main():
        data = fetch_bootstrap_static()
        fixtures = fetch_fixtures()
        print("Keys:", list(data.keys()))
        print("Players:", len(data["elements"]))
        print("Teams:", len(data["teams"]))

if __name__ == "__main__":
    main()