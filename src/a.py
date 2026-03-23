from shared.db.connection import default_engine

with default_engine.connect() as conn:
    print("DB connection OK")
