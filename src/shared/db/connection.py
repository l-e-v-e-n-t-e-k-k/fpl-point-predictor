from sqlalchemy import create_engine
import os
from pathlib import Path

SCHEMA_PATH = Path("shared/db/schemas.sql")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mluser:mlpass@localhost:5432/fpldb"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)