import os

from sqlalchemy import create_engine


DEFAULT_S1_DATABASE_URL = "postgresql://mluser:mlpass@localhost:5432/rawdb"
DEFAULT_S2_DATABASE_URL = "postgresql://mluser:mlpass@localhost:5433/featuredb"


def build_engine(url: str):
    return create_engine(url, pool_pre_ping=True)


S1_DATABASE_URL = os.getenv(
    "S1_DATABASE_URL",
    DEFAULT_S1_DATABASE_URL,
)
S2_DATABASE_URL = os.getenv(
    "S2_DATABASE_URL",
    DEFAULT_S2_DATABASE_URL,
)

raw_engine = build_engine(S1_DATABASE_URL)
feature_engine = build_engine(S2_DATABASE_URL)

# Backward compatibility only.
engine = raw_engine
