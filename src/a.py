from shared.db.connection import engine

with engine.connect() as conn:
    print("DB connection OK")