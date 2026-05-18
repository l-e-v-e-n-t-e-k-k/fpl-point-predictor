import os
import json
import logging

import pandas as pd
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from S2.add_target import add_target, save_supervised
from S2.build_dataset_multiseason import build_multiseason, save_multiseason, save_multiseason_db
from S2.build_dataset_pandas import build_current_season, save_current_season
from S2.merge_difficulty import merge_difficulty, save_with_difficulty
from shared.db.connection import feature_engine

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("S2")

FEATURE_TABLE_NAME = os.getenv("FEATURE_TABLE_NAME", "player_data")
SAVE_LOCAL = os.getenv("SAVE_LOCAL", "false").lower() == "true"


class HealthResponse(BaseModel):
    status: str
    feature_table: str
    db_role: str


class TrainingDatasetResponse(BaseModel):
    source_endpoint: str
    feature_table: str
    row_count: int
    columns: list[str]
    data: list[dict]


def items(df: pd.DataFrame):
    return json.loads(df.to_json(orient="records", date_format="iso"))

def run_pipeline():
    current_raw_df = build_current_season()
    current_with_difficulty_df = merge_difficulty(current_raw_df)
    current_supervised_df = add_target(current_with_difficulty_df)
    multiseason_df = build_multiseason(current_supervised_df)

    if SAVE_LOCAL:
        save_current_season(current_raw_df)
        save_with_difficulty(current_with_difficulty_df)
        save_supervised(current_supervised_df)
        save_multiseason(multiseason_df)

    save_multiseason_db(multiseason_df, table_name=FEATURE_TABLE_NAME)

    return {
        "status": "ok",
        "feature_table": FEATURE_TABLE_NAME,
        "current_rows": len(current_raw_df),
        "current_with_difficulty_rows": len(current_with_difficulty_df),
        "current_supervised_rows": len(current_supervised_df),
        "multiseason_rows": len(multiseason_df),
        "columns": list(multiseason_df.columns),
    }


@app.get("/healthz", response_model=HealthResponse)
def healthz():
    return {"status": "ok", "feature_table": FEATURE_TABLE_NAME, "db_role": "feature"}


@app.get("/readyz", response_model=HealthResponse)
def readyz():
    try:
        with feature_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"feature db not ready: {exc}") from exc

    return {"status": "ready", "feature_table": FEATURE_TABLE_NAME, "db_role": "feature"}

#  --- S3 endpoint ---
@app.get("/training-dataset", response_model=TrainingDatasetResponse)
def get_training_dataset(limit: int | None = None):
    try:
        df = pd.read_sql(f"SELECT * FROM {FEATURE_TABLE_NAME}", feature_engine)

        if limit is not None:
            df = df.head(limit)

        logger.info("S2 training-dataset rows: %s", len(df))
        return {
            "source_endpoint": "/training-dataset",
            "feature_table": FEATURE_TABLE_NAME,
            "row_count": len(df),
            "columns": list(df.columns),
            "data": items(df),
        }
    except Exception as exc:
        logger.error("S2 training-dataset query failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to query training dataset.") from exc

#  --- S4 endpoint ---
@app.get("/player-data/latest")
def get_latest_player_data():
    query = f"""
    SELECT *
    FROM {FEATURE_TABLE_NAME}
    WHERE season = (
        SELECT MAX(season) FROM {FEATURE_TABLE_NAME}
    )
    AND "GW" = (
        SELECT MAX("GW")
        FROM {FEATURE_TABLE_NAME}
        WHERE season = (
            SELECT MAX(season) FROM {FEATURE_TABLE_NAME}
        )
    )
    """
    try:
        df = pd.read_sql(query, feature_engine)
        logger.info("S2 latest feature rows: %s", len(df))
        return {"data": items(df)}
    except Exception as exc:
        logger.error("S2 latest feature query failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to query latest feature data.") from exc


@app.post("/run")
def run():
    try:
        logger.info("S2 pipeline started")
        result = run_pipeline()
        logger.info("S2 pipeline finished: %s", result)
        return result
    except Exception as exc:
        logger.error("S2 pipeline failed: %s", exc)
        raise HTTPException(status_code=500, detail="Feature pipeline execution failed.") from exc
