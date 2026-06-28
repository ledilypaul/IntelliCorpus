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
    """Open a PDF from bytes and extract text, metadata and page count.

    Args:
        pdf_bytes: raw PDF content as bytes.

    Returns:
        dict with keys: num_pages (int), pages (list of {page_number, text}), metadata (dict).
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


def extract_pdf(minio_path: str) -> dict:
    """Full pipeline: download from MinIO → extract with PyMuPDF → clean text.

    Args:
        minio_path: object path in MinIO bucket.

    Returns:
        dict with keys:
          - status: 'ok' or 'failed'
          - minio_path: source path
          - num_pages, metadata, pages: present if status == 'ok'
          - cleaned_text: full cleaned text joined from all pages, ready for chunking
          - error: error message if status == 'failed'
    """
    from ai_pipelines.text_cleaner import clean_text, remove_repeated_headers_footers
    try:
        pdf_bytes = download_pdf_bytes(minio_path)
        extracted = extract_text_from_pdf(pdf_bytes)

        raw_pages = [p["text"] for p in extracted["pages"]]
        clean_pages = remove_repeated_headers_footers(raw_pages)
        cleaned_text = "\n\n".join(clean_text(page) for page in clean_pages)

        return {
            "status": "ok",
            "minio_path": minio_path,
            "num_pages": extracted["num_pages"],
            "metadata": extracted["metadata"],
            "pages": extracted["pages"],
            "cleaned_text": cleaned_text,
        }

    except Exception as e:
        return {
            "status": "failed",
            "minio_path": minio_path,
            "error": str(e),
        }