from tempfile import TemporaryFile

from minio import Minio

from storage.minio_client import get_minio_client, object_exists, BUCKET_NAME


def download_pdf_to_tempfile(minio_path) -> TemporaryFile:
    """Download a pdf from minio and return as a Temporary fileÒ
    """
    bucket_name, object_name = minio_path.split("/", 1)

    tmp = TemporaryFile()

    client = get_minio_client()
    response = client.get_object(bucket_name, object_name)
    tmp.write(response.read())
    tmp.seek(0)  # important : remettre le curseur au début

    return tmp

def extract_text_from_pdf(pdf_path) -> dict:
    return 0