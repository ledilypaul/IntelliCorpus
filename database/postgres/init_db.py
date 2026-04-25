from sqlalchemy import text
from sqlalchemy.engine import Engine

SCHEMAS = ["corpus"]


def init_schemas(engine: Engine) -> None:
    with engine.connect() as conn:
        for schema in SCHEMAS:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.commit()
