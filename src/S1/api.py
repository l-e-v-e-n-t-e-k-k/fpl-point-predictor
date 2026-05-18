import json
import logging

import pandas as pd
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from S1.main import run_pipeline
from shared.db.connection import raw_engine

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("S1")


class HealthResponse(BaseModel):
    status: str
    db_role: str


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


@app.get("/healthz", response_model=HealthResponse)
def healthz():
    return {"status": "ok", "db_role": "raw"}


@app.get("/readyz", response_model=HealthResponse)
def readyz():
    try:
        with raw_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"raw db not ready: {exc}") from exc

    return {"status": "ready", "db_role": "raw"}


@app.post("/run")
def run():
    try:
        logger.info("S1 pipeline started")
        result = run_pipeline()
        logger.info("S1 pipeline finished: %s", result)
        return result
    except Exception as exc:
        logger.error("S1 pipeline failed: %s", exc)
        raise HTTPException(status_code=500, detail="Ingestion pipeline execution failed.") from exc


@app.get("/current-season")
def get_current_season():
    try:
        df = current_season_df()
        logger.info("S1 current-season rows: %s", len(df))
        return {"data": items(df)}
    except Exception as exc:
        logger.error("S1 current-season query failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to query current season data.") from exc


@app.get("/fixtures")
def get_fixtures():
    try:
        df = fixtures_df()
        logger.info("S1 fixtures rows: %s", len(df))
        return {"data": items(df)}
    except Exception as exc:
        logger.error("S1 fixtures query failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to query fixture data.") from exc


@app.get("/player-meta")
def get_player_meta():
    try:
        df = player_meta_df()
        logger.info("S1 player-meta rows: %s", len(df))
        return {"data": items(df)}
    except Exception as exc:
        logger.error("S1 player-meta query failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to query player metadata.") from exc
