from io import BytesIO

import fitz

from storage.minio_client import get_minio_client, object_exists, BUCKET_NAME


def download_pdf_bytes(minio_path : str) -> bytes:
    """Download a pdf from minio and return its raw Bytes
    """
    client = get_minio_client()
    response = client.get_object(BUCKET_NAME, minio_path)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()

def extract_text_from_pdf(pdf_bytes: bytes) -> dict:
    """Open a PDF from bytes and extract text per page
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    pages = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        pages.append({
            "page_number": page_num,
            "text": text,
        })
    metadata = doc.metadata
    num_pages = len(doc)
    doc.close()
    
    return {
        "num_pages": num_pages,
        "pages": pages,
        "metadata": metadata,
    }