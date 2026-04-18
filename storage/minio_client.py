import os
from datetime import timedelta

from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error


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

def download_pdf(object_name: str, destination_path: str) -> None:
    """Download a PDF from MinIO to a local path."""
    client = get_minio_client()
    client.fget_object(BUCKET_NAME, object_name, destination_path)

def object_exists(object_name: str) -> bool:
    """Check if an object already exists in MinIO."""
    client = get_minio_client()
    try:
        client.stat_object(BUCKET_NAME, object_name)
        return True
    except S3Error as e:
        if e.code == "NoSuchKey":
            return False
        raise
    
def get_pdf_url(object_name: str, expires_hours: int = 1) -> str:
    """Generate a presigned URL to access a PDF temporarily."""
    from datetime import timedelta
    client = get_minio_client()
    return client.presigned_get_object(BUCKET_NAME, object_name, expires=timedelta(hours=expires_hours))


def delete_pdf(object_name: str) -> None:
    client = get_minio_client()
    client.remove_object(BUCKET_NAME, object_name)
