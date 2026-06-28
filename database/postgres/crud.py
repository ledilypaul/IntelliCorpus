from datetime import datetime, timezone

from sqlalchemy import Table, select, update
from sqlalchemy.dialects.postgresql import insert

def upsert_data(data : list[dict], index_elements : list[str], table : Table, engine):
    """Insert rows into a table, updating them on conflict (upsert).

    If a row's index_elements already exist in the table, all other columns
    are overwritten with the new values. If index_elements cover every
    column (nothing left to update), the conflicting row is left untouched.

    Args:
        data (list[dict]): rows to insert, one dict per row.
        index_elements (list[str]): column names that define the unique
            constraint to detect conflicts on (e.g. the primary key).
        table (Table): SQLAlchemy table to insert into.
        engine: SQLAlchemy engine used to open the connection.
    """
    with engine.begin() as conn:
        #Insertion query for PostgresSQL
        stmt = insert(table).values(data)
        
        # On crée un dictionnaire qui dit : "Pour chaque colonne (sauf l'id), 
        # prends la nouvelle valeur qui a été 'exclue' et mets la à jour."
        update_dict = {
            col.name: getattr(stmt.excluded, col.name) #Pour créer des paires clé/valeur 
            for col in stmt.excluded if col.name not in index_elements
        }

        if update_dict:
            stmt = stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_=update_dict
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)
        
        conn.execute(stmt)
        print(f"{len(data)} succesfuly treated inside table {table}")


def get_articles_without_pdf(engine, table: Table) -> list[dict]:
    """Fetch articles that have a PDF URL but no PDF downloaded yet.

    Args:
        engine: SQLAlchemy engine used to open the connection.
        table (Table): document table to query.

    Returns:
        list[dict]: rows where minio_path is null, pdf_url is set and
            pdf_status == "pending".
    """
    with engine.connect() as conn:
        stmt = select(table).where(
            table.c.minio_path == None,
            table.c.pdf_url != None,
            table.c.pdf_status == "pending"
        )
        return conn.execute(stmt).mappings().all()

def get_articles_with_pdf(engine, file_status,table: Table) -> list[dict]:
    """Fetch articles whose PDF is downloaded but not yet ingested into the RAG pipeline.

    Args:
        engine: SQLAlchemy engine used to open the connection.
        table (Table): document table to query.

    Returns:
        list[dict]: rows where minio_path is set, pdf_status == "downloaded"
            and rag_status == "pending".
    """
    with engine.connect() as conn:
        stmt = select(table).where(
            table.c.minio_path != None,
            table.c.pdf_status == "downloaded",
            table.c.rag_status == file_status
        )
        return conn.execute(stmt).mappings().all()

def update_pdf_fields(engine, table: Table, article_id: str, minio_path: str | None, pdf_status: str, pdf_size_bytes: int = None, pdf_sha256: str = None ) -> None:
    """Update the PDF-related columns of a single article after a download attempt.

    Args:
        engine: SQLAlchemy engine used to open the connection.
        table (Table): document table to update.
        article_id (str): id of the article to update.
        minio_path (str | None): object path in MinIO, or None if the download failed.
        pdf_status (str): new pdf_status value (e.g. "downloaded", "failed").
        pdf_size_bytes (int, optional): size of the downloaded PDF in bytes.
        pdf_sha256 (str, optional): SHA-256 checksum of the downloaded PDF.
    """
    with engine.begin() as conn:
        stmt = update(table).where(table.c.id == article_id).values(
            minio_path=minio_path,
            pdf_status=pdf_status,
            pdf_downloaded_at=datetime.now(timezone.utc),
            pdf_size_bytes=pdf_size_bytes,
            pdf_sha256=pdf_sha256
        )
        conn.execute(stmt)


def update_rag_status(engine, table: Table, article_id: str, rag_status: str) -> None:
    """Update the rag_status column of a single article.

    Args:
        engine: SQLAlchemy engine used to open the connection.
        table (Table): document table to update.
        article_id (str): id of the article to update.
        rag_status (str): new rag_status value (e.g. "embedded", "failed").
    """
    with engine.begin() as conn:
        stmt = update(table).where(table.c.id == article_id).values(rag_status=rag_status)
        conn.execute(stmt)