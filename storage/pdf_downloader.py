import hashlib
from datetime import datetime
from io import BytesIO

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from database.postgres.crud import get_articles_without_pdf, update_pdf_fields
from storage.minio_client import get_minio_client, object_exists, BUCKET_NAME


def _build_object_name(
    source: str, 
    article_id: str, 
    published_at=None
) -> str:
    # Construit le chemin de stockage dans MinIO : source/YYYY/MM/uuid.pdf
    # published_at peut être un datetime ou None (fallback sur la date du jour)
    if published_at:
        YYYY = published_at.strftime("%Y")
        MM = published_at.strftime("%m")
    else:
        now = datetime.now()
        YYYY = now.strftime("%Y")
        MM = now.strftime("%m")
    return f"{source}/{YYYY}/{MM}/{article_id}.pdf"


def _fetch_pdf_bytes(pdf_url: str) -> bytes:
    # Crée une session HTTP avec retry automatique
    # Retry : 3 tentatives, sur les erreurs 500/502/503/504, avec backoff (attend 1s, 2s, 4s entre chaque essai)
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)

    r = session.get(pdf_url, timeout=30, headers={"User-Agent": "IntelliCorpus/1.0"})
    r.raise_for_status()

    # Vérifie que le serveur renvoie bien un PDF et non une page HTML
    # (arXiv et d'autres peuvent rediriger vers du HTML si l'URL est mauvaise)
    content_type = r.headers.get("Content-Type", "")
    if "pdf" not in content_type:
        raise ValueError(f"Content-Type inattendu '{content_type}' pour {pdf_url}")

    return r.content


def _compute_sha256(pdf_bytes: bytes) -> str:
    # Calcule une empreinte unique du fichier
    # Utile pour détecter si un PDF a changé ou pour éviter les doublons
    return hashlib.sha256(pdf_bytes).hexdigest()


def download_and_store(article: dict, engine, table) -> None:
    object_name = _build_object_name(
        source=article["source"],
        article_id=article["id"],
        published_at=article.get("published_at"),
    )

    # Idempotence : si le fichier est déjà dans MinIO, on ne re-télécharge pas
    if object_exists(object_name):
        print(f"  SKIP (déjà présent) {object_name}")
        update_pdf_fields(engine, table, article["id"], object_name, "downloaded")
        return

    pdf_bytes = _fetch_pdf_bytes(article["pdf_url"])
    sha256 = _compute_sha256(pdf_bytes)

    client = get_minio_client()
    client.put_object(
        BUCKET_NAME,
        object_name,
        BytesIO(pdf_bytes),
        length=len(pdf_bytes),
        content_type="application/pdf",
    )

    update_pdf_fields(
        engine=engine,
        table=table,
        article_id=article["id"],
        minio_path=object_name,
        pdf_status="downloaded",
        pdf_size_bytes=len(pdf_bytes),
        pdf_sha256=sha256,
    )
    print(f"  OK {article['title'][:60]}")


def run_pdf_pipeline(engine, table) -> None:
    articles = get_articles_without_pdf(engine, table)
    print(f"{len(articles)} PDFs à télécharger...")
    for article in articles:
        try:
            download_and_store(article, engine, table)
        except Exception as e:
            update_pdf_fields(engine, table, article["id"], None, "failed")
            print(f"  FAILED {article['id']}: {e}")
