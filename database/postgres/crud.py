from datetime import datetime, timezone

from sqlalchemy import Table, Column, String, Text, DateTime, MetaData, JSON, select, update
from sqlalchemy.dialects.postgresql import insert

def upsert_data(data : list[dict], index_elements : list[str], table : Table, engine):
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
    with engine.connect() as conn:
        stmt = select(table).where(
            table.c.minio_path == None,
            table.c.pdf_url != None,
            table.c.pdf_status == "pending"
        )
        return conn.execute(stmt).mappings().all()


def update_pdf_fields(engine, table: Table, article_id: str, minio_path: str | None, pdf_status: str, pdf_size_bytes: int = None) -> None:
    with engine.begin() as conn:
        stmt = update(table).where(table.c.id == article_id).values(
            minio_path=minio_path,
            pdf_status=pdf_status,
            pdf_downloaded_at=datetime.now(timezone.utc),
            pdf_size_bytes=pdf_size_bytes,
        )
        conn.execute(stmt)