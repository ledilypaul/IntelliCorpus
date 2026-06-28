"""
Pipeline d'ingestion RAG : extract -> chunk -> embed -> store.

Itère sur les documents dont le PDF est téléchargé mais pas encore vectorisé
(pdf_status='downloaded' AND rag_status='pending'), et met à jour rag_status
en fonction du résultat ('embedded' ou 'failed').
"""
from ai_pipelines.chunker import split_text
from ai_pipelines.embedders import embed_batch
from ai_pipelines.pdf_extractor import extract_pdf
from ai_pipelines.tokenizer import count_tokens
from ai_pipelines.vector_store import upsert_chunks
from config.db_engine import get_db_engine
from database.postgres.crud import get_articles_with_pdf, update_rag_status
from models.postgres.corpus_schema import document_table

ENCODING_NAME = "cl100k_base"


def _build_chunk_records(document_id: str, chunks: list[str], vectors: list[list[float]]) -> list[dict]:
    """Pair chunk texts with their embeddings into chunk_table rows."""
    return [
        {
            "id": f"{document_id}:{i}",
            "document_id": document_id,
            "chunk_index": i,
            "content": chunk,
            "token_count": count_tokens(chunk, ENCODING_NAME),
            "embedding": vector,
            "section": None,
        }
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]


def ingest_document(engine, document: dict) -> str:
    """Process a single document: extract -> chunk -> embed -> store.

    Args:
        engine: SQLAlchemy engine.
        document: row from document_table, must contain 'id' and 'minio_path'.

    Returns:
        The resulting rag_status: 'embedded' or 'failed'.
    """
    extracted = extract_pdf(document["minio_path"])
    if extracted["status"] == "failed":
        print(f"    extraction failed for {document['id']}: {extracted.get('error')}")
        update_rag_status(engine, document_table, document["id"], "failed")
        return "failed"

    chunks = split_text(extracted["cleaned_text"])
    if not chunks:
        text_len = len(extracted["cleaned_text"])
        print(f"    no chunks produced for {document['id']} (cleaned_text length={text_len})")
        update_rag_status(engine, document_table, document["id"], "failed")
        return "failed"

    vectors = embed_batch(chunks)
    chunk_records = _build_chunk_records(document["id"], chunks, vectors)
    upsert_chunks(chunk_records)

    update_rag_status(engine, document_table, document["id"], "embedded")
    return "embedded"


def ingest_pending_documents(engine=None) -> dict:
    """Ingest all documents with pdf_status='downloaded' AND rag_status='pending'.

    Returns:
        dict with counts: {"embedded": int, "failed": int}.
    """
    engine = engine or get_db_engine()
    documents = get_articles_with_pdf(engine, "pending",document_table)
    print(f"{len(documents)} documents to ingest...")

    results = {"embedded": 0, "failed": 0}
    for document in documents:
        try:
            status = ingest_document(engine, document)
        except Exception as e:
            update_rag_status(engine, document_table, document["id"], "failed")
            status = "failed"
            print(f"  FAILED {document['id']}: {e}")
        else:
            print(f"  {status.upper()} {document['title'][:60]}")
        results[status] += 1

    return results

def ingest_failed_documents(engine=None) -> dict:
    """Ingest all documents with pdf_status='downloaded' AND rag_status='failed'.

    Args:
        engine (_type_, optional): _description_. Defaults to None.

    Returns:
        dict: _description_
    """
    engine = engine or get_db_engine()
    documents = get_articles_with_pdf(engine, "failed",document_table)
    print(f"{len(documents)} documents to ingest")

    results = {"embedded": 0, "failed": 0}
    for document in documents:
        try:
            status = ingest_document(engine, document)
        except Exception as e:
            update_rag_status(engine, document_table, document["id"], "failed")
            status = "failed"
            print(f"  FAILED {document['id']}: {e}")
        else:
            print(f"  {status.upper()} {document['title'][:60]}")
        results[status] += 1

    return results