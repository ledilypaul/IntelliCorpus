import os
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = "intellicorpus-pdfs"

_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ROOT_USER"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
            secure=False,
        )
        _ensure_bucket(_client)
    return _client


def _ensure_bucket(client: Minio) -> None:
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)


def upload_pdf(article_id: str, source: str, pdf_path: str) -> str:
    """Upload a PDF file and return its MinIO object path."""
    client = get_minio_client()
    object_name = f"{source}/{article_id}.pdf"
    client.fput_object(BUCKET_NAME, object_name, pdf_path, content_type="application/pdf")
    return object_name


def download_pdf(object_name: str, destination_path: str) -> None:
    """Download a PDF from MinIO to a local path."""
    client = get_minio_client()
    client.fget_object(BUCKET_NAME, object_name, destination_path)


def get_pdf_url(object_name: str, expires_hours: int = 1) -> str:
    """Generate a presigned URL to access a PDF temporarily."""
    from datetime import timedelta
    client = get_minio_client()
    return client.presigned_get_object(BUCKET_NAME, object_name, expires=timedelta(hours=expires_hours))


def delete_pdf(object_name: str) -> None:
    client = get_minio_client()
    client.remove_object(BUCKET_NAME, object_name)
