from shared.db.connection import raw_engine

DROP_SQL = """
DROP TABLE IF EXISTS raw.player_history;
DROP TABLE IF EXISTS raw.fixtures;
DROP TABLE IF EXISTS raw.players;
DROP TABLE IF EXISTS raw.teams;
"""


def reset_db():
    with raw_engine.begin() as conn:
        conn.exec_driver_sql(DROP_SQL)

    print("Database schema reset.")


if __name__ == "__main__":
    reset_db()
