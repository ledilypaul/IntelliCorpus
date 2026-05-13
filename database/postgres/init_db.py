from sqlalchemy import text
from sqlalchemy.engine import Engine

SCHEMAS = ["corpus"]


def init_extensions(engine: Engine) -> None:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()


def init_schemas(engine: Engine) -> None:
    with engine.connect() as conn:
        for schema in SCHEMAS:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.commit()


def init_indexes(engine: Engine) -> None:
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS chunk_embedding_hnsw_idx
            ON corpus.chunk USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """))
        conn.commit()
