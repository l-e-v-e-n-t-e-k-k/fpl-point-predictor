import json

import pandas as pd
from fastapi import FastAPI
from fastapi import HTTPException
from sqlalchemy import text

from S1.main import run_pipeline
from shared.db.connection import raw_engine

app = FastAPI()


def items(df: pd.DataFrame):
    return json.loads(df.to_json(orient="records", date_format="iso"))


def current_season_df():
    query = """
    SELECT
        ph.player_id,
        ph.round AS "GW",
        ph.minutes,
        ph.total_points,
        ph.clean_sheets,
        ph.bps,
        ph.saves,
        ph.expected_goals,
        ph.expected_assists,
        ph.expected_goals_conceded,
        ph.value,
        ph.was_home,
        ph.opponent_team,
        ph.fixture,
        f.team_h,
        f.team_a,
        CONCAT(p.first_name, ' ', p.second_name) AS name,
        CASE
            WHEN p.element_type = 1 THEN 'GKP'
            WHEN p.element_type = 2 THEN 'DEF'
            WHEN p.element_type = 3 THEN 'MID'
            WHEN p.element_type = 4 THEN 'FWD'
        END AS position
    FROM raw.player_history ph
    JOIN raw.players p
        ON ph.player_id = p.id
    LEFT JOIN raw.fixtures f
        ON ph.fixture = f.id
    ORDER BY ph.player_id, ph.round, ph.fixture
    """
    return pd.read_sql(query, raw_engine)


def fixtures_df():
    query = """
    SELECT
        id,
        event,
        kickoff_time,
        team_h,
        team_a,
        team_h_difficulty,
        team_a_difficulty,
        finished
    FROM raw.fixtures
    ORDER BY id
    """
    return pd.read_sql(query, raw_engine)


def player_meta_df():
    query = """
    SELECT
        CONCAT(p.first_name, ' ', p.second_name) AS name,
        p.first_name,
        p.second_name,
        p.web_name,
        p.element_type,
        p.now_cost,
        t.name AS team_name
    FROM raw.players p
    LEFT JOIN raw.teams t
        ON p.team = t.id
    ORDER BY p.id
    """
    return pd.read_sql(query, raw_engine)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "db_role": "raw"}


@app.get("/readyz")
def readyz():
    try:
        with raw_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"raw db not ready: {exc}") from exc

    return {"status": "ready", "db_role": "raw"}


@app.post("/run")
def run():
    return run_pipeline()


@app.get("/current-season")
def get_current_season():
    df = current_season_df()
    return {"data": items(df)}


@app.get("/fixtures")
def get_fixtures():
    df = fixtures_df()
    return {"data": items(df)}


@app.get("/player-meta")
def get_player_meta():
    df = player_meta_df()
    return {"data": items(df)}
