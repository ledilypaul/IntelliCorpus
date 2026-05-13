from dotenv import load_dotenv
load_dotenv()

from config.db_engine import get_db_engine
from config_info import APIS
from database.postgres.crud import get_articles_without_pdf, update_pdf_fields, upsert_data
from database.postgres.init_db import init_extensions, init_indexes, init_schemas
from models.postgres.corpus_schema import document_table, chunk_table, metadata
from processing.cleaning_data import normalize_data
from scrapers.arxiv import parser_arxiv
from scrapers.basic_fetching import fetch_raw
from storage.minio_client import upload_pdf_from_url


def init_db(engine):
    init_extensions(engine)
    init_schemas(engine)
    metadata.create_all(engine)
    init_indexes(engine)


def scraping_data(engine, search_key, quantity):
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


if __name__ == "__main__":
    engine = get_db_engine()
    init_db(engine)
    scraping_data(engine, "Artificial Intelligence NLP", 10)
    download_pdfs(engine)
