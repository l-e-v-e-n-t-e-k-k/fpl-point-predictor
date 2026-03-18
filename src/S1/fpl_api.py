#fpl_api.py
from pathlib import Path
from S1.data_utils import download_json
from shared.db.connection import engine
import pandas as pd

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

def save_players(data: dict):
    players = pd.DataFrame(data["elements"])[
        [
            "id",
            "web_name",
            "first_name",
            "second_name",
            "team",
            "element_type",
            "now_cost",
            "total_points",
        ]
    ]

    with engine.begin() as conn:
        conn.exec_driver_sql("TRUNCATE TABLE raw.players CASCADE")

    players.to_sql(
        "players",
        engine,
        schema="raw",
        if_exists="append",
        index=False
    )


def save_teams(data: dict):
    teams = pd.DataFrame(data["teams"])[
        [
            "id",
            "name",
            "short_name",
        ]
    ]

    with engine.begin() as conn:
        conn.exec_driver_sql("TRUNCATE TABLE raw.teams CASCADE")

    teams.to_sql(
        "teams",
        engine,
        schema="raw",
        if_exists="append",
        index=False
    )


def save_fixtures(fixtures: list):
    df = pd.DataFrame(fixtures)[
        [
            "id",
            "event",
            "kickoff_time",
            "team_h",
            "team_a",
            "team_h_score",
            "team_a_score",
            "team_h_difficulty",
            "team_a_difficulty",
            "finished",
        ]
    ]

    df["kickoff_time"] = pd.to_datetime(df["kickoff_time"], utc=True)

    with engine.begin() as conn:
        conn.exec_driver_sql("TRUNCATE TABLE raw.fixtures CASCADE")

    df.to_sql(
        "fixtures",
        engine,
        schema="raw",
        if_exists="append",
        index=False
    )

def main():
        data = fetch_bootstrap_static()
        fixtures = fetch_fixtures()
        
        save_teams(data)
        save_players(data)
        
        save_fixtures(fixtures)
        print("Keys:", list(data.keys()))
        print("Players:", len(data["elements"]))
        print("Teams:", len(data["teams"]))

if __name__ == "__main__":
    main()
