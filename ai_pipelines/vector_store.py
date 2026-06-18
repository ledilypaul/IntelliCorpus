from sqlalchemy import text

from config.db_engine import get_db_engine
from database.postgres.crud import upsert_data
from models.postgres.corpus_schema import chunk_table


def upsert_chunks(chunks: list[dict]):
    """Insert or update chunks in the chunk table.

    Each dict must contain:
        id            (str)       unique chunk identifier
        document_id   (str)       FK to corpus.document
        chunk_index   (int)       position of the chunk in the document
        content       (str)       chunk text
        token_count   (int)       number of tokens
        embedding     (list[float]) vector of dim EMBEDDING_DIM
        section       (str | None) optional section label
    """
    if not chunks:
        return
    upsert_data(
        data=chunks,
        index_elements=["id"],
        table=chunk_table,
        engine=get_db_engine(),
    )


def search(query_vector: list[float], k: int = 5) -> list[dict]:
    """Return the k most similar chunks to query_vector (cosine similarity).

    Args:
        query_vector: embedding of the query, same dim as stored embeddings.
        k: number of results to return.

    Returns:
        list of dicts with keys: id, document_id, chunk_index, content,
        token_count, score (cosine similarity in [0, 1]).
    """
    # pgvector expects the vector as a string "[x, y, z, ...]" in raw SQL
    qvec_str = str(query_vector)

    sql = text("""
        SELECT id, document_id, chunk_index, content, token_count,
               1 - (embedding <=> CAST(:qvec AS vector)) AS score
        FROM corpus.chunk
        ORDER BY embedding <=> CAST(:qvec AS vector)
        LIMIT :k
    """)
    with get_db_engine().connect() as conn:
        rows = conn.execute(sql, {"qvec": qvec_str, "k": k}).mappings().all()
    return [dict(r) for r in rows]
