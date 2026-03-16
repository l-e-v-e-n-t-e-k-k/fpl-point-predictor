from sqlalchemy import create_engine

DATABASE_URL = "postgresql://mluser:mlpass@localhost:5432/fpldb"

engine = create_engine(DATABASE_URL)