import os
import json

import pandas as pd
from fastapi import FastAPI

from S2.add_target import add_target, save_supervised
from S2.build_dataset_multiseason import build_multiseason, save_multiseason, save_multiseason_db
from S2.build_dataset_pandas import build_current_season, save_current_season
from S2.merge_difficulty import merge_difficulty, save_with_difficulty
from shared.db.connection import feature_engine

app = FastAPI()

FEATURE_TABLE_NAME = os.getenv("FEATURE_TABLE_NAME", "player_data")
SAVE_LOCAL = os.getenv("SAVE_LOCAL", "false").lower() == "true"


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


@app.get("/healthz")
def healthz():
    return {"status": "ok", "feature_table": FEATURE_TABLE_NAME, "db_role": "feature"}

# --- S3 endpoint ---
@app.get("/player-data")
def get_player_data(limit: int | None = None):
    df = pd.read_sql(f"SELECT * FROM {FEATURE_TABLE_NAME}", feature_engine)

    if limit is not None:
        df = df.head(limit)

    return {"data": items(df)}

# --- S4 endpoint ---
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
    df = pd.read_sql(query, feature_engine)
    return {"data": items(df)}


@app.post("/run")
def run():
    return run_pipeline()
