from sqlalchemy import Table, Column, String, Text, DateTime, MetaData, JSON, BigInteger, func

metadata = MetaData()

document_table = Table(
    "document",
    metadata,
    Column("id", String, primary_key=True), # L'URL arXiv sert d'ID unique
    Column("source", String),
    Column("source_url",String),

    # Article Metadata
    Column("title", String, nullable=False),
    Column("summary", Text),
    Column("authors", JSON), # Stocke la liste ['Author 1', 'Author 2']
    Column("published_at", DateTime),
    Column("uri", String),
    Column("pdf_url", String),

    Column("minio_path", String, nullable=True), # ex: arxiv/2026/04/<uuid>.pdf
    Column("pdf_status", String, default="pending"),   # pending/downloaded/failed/unavailable
    Column("pdf_downloaded_at", DateTime, nullable=True),
    Column("pdf_size_bytes", BigInteger, nullable=True),
    Column("pdf_sha256", String, nullable=True),
    
    Column("created_at", DateTime, server_default=func.now()),
    Column("updated_at", DateTime, onupdate=func.now()),
    
    schema='corpus'
)