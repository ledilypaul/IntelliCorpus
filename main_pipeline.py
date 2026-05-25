from dotenv import load_dotenv
load_dotenv()

import polars as pl
from sqlalchemy import select

from ai_pipelines.pdf_extractor import download_pdf_bytes, extract_text_from_pdf
from ai_pipelines.text_cleaner import clean_text, remove_repeated_headers_footers
from config.db_engine import get_db_engine
from config_info import APIS
from database.postgres.crud import get_articles_without_pdf, get_articles_with_pdf, update_pdf_fields, upsert_data
from database.postgres.init_db import init_extensions, init_indexes, init_schemas
from models.postgres.corpus_schema import document_table, chunk_table, metadata
from processing.cleaning_data import normalize_data
from scrapers.arxiv import parser_arxiv
from scrapers.basic_fetching import fetch_raw
from storage.minio_client import upload_pdf_from_url


def init_db(engine):
    """Initialize the database: extensions, schemas, tables and indexes."""
    init_extensions(engine)
    init_schemas(engine)
    metadata.create_all(engine)
    init_indexes(engine)


def scraping_data(engine, search_key, quantity):
    """Fetch articles from arXiv and upsert them into the document table."""
    print(f"Fetching arXiv: '{search_key}' ({quantity} results)...")
    raw_result = fetch_raw(APIS["arXiv"]["api_url"].format(query=search_key, quantity=quantity))
    result_arxiv = parser_arxiv(raw_result)
    clean_arxiv_data = normalize_data(
        raw_data=result_arxiv,
        source_name="arXiv",
        date_columns=["published_at"],
        columns_drop=["updated"]
    )
    upsert_data(clean_arxiv_data, ["id"], document_table, engine)


def download_pdfs(engine):
    """Download pending PDFs and upload them to MinIO."""
    articles = get_articles_without_pdf(engine, document_table)
    print(f"{len(articles)} PDFs to download...")
    for article in articles:
        try:
            minio_path, size = upload_pdf_from_url(article["id"], article["source"], article["pdf_url"])
            update_pdf_fields(engine, document_table, article["id"], minio_path, "downloaded", size)
            print(f"  OK {article['title'][:60]}")
        except Exception as e:
            update_pdf_fields(engine, document_table, article["id"], None, "failed")
            print(f"  FAILED {article['id']}: {e}")


def inspect_documents(columns: list[str] = None) -> pl.DataFrame:
    """Query the document table and return results as a Polars DataFrame.

    Args:
        columns: list of column names to select. Returns all columns if None.
    """
    engine = get_db_engine()
    with engine.connect() as conn:
        cols = [document_table.c[col] for col in columns] if columns else [document_table]
        result = conn.execute(select(*cols)).mappings().all()
    return pl.DataFrame([dict(r) for r in result])


def extract_and_clean_pdf(minio_path: str) -> list[str]:
    """Download a PDF from MinIO, extract its text and return cleaned pages.

    Args:
        minio_path: object path in MinIO bucket.

    Returns:
        List of cleaned text strings, one per page.
    """
    pdf_bytes = download_pdf_bytes(minio_path)
    pdf_data = extract_text_from_pdf(pdf_bytes)
    raw_pages = [page["text"] for page in pdf_data["pages"]]
    pages = remove_repeated_headers_footers(raw_pages)
    return [clean_text(page) for page in pages]


def test_pdf_extractor():
    """Pick the first document with a stored PDF and print its cleaned text page by page."""
    df = inspect_documents(columns=["id", "title", "minio_path"])
    doc = df.filter(pl.col("minio_path").is_not_null()).row(0, named=True)
    print(f"Document: {doc['title']}")

    cleaned_pages = extract_and_clean_pdf(doc["minio_path"])

    for i, page in enumerate(cleaned_pages, start=1):
        print(f"\n--- Page {i} ---")
        print(page)
    
if __name__ == "__main__":
    # engine = get_db_engine()
    # init_db(engine)
    # scraping_data(engine, "Artificial Intelligence NLP", 10)
    # download_pdfs(engine)
    test_pdf_extractor()