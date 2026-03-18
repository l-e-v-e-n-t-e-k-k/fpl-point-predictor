from pathlib import Path
from shared.db.connection import engine

SCHEMA_PATH = Path("src/shared/db/schemas.sql")

def init_db():
    sql = SCHEMA_PATH.read_text(encoding="utf-8")

    with engine.begin() as conn:
        conn.exec_driver_sql(sql)

    print("Database schema created.")

if __name__ == "__main__":
    init_db()