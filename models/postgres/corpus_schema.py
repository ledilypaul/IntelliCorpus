from sqlalchemy import Table, Column, String, Text, DateTime, MetaData, JSON, BigInteger, Integer, ForeignKey, func
from pgvector.sqlalchemy import Vector

EMBEDDING_DIM = 384   # OpenAI text-embedding-3-small / ada-002

metadata = MetaData()

document_table = Table(
    "document",
    metadata,
    Column("id", String, primary_key=True),
    Column("source", String),
    Column("source_url", String),
    Column("title", String, nullable=False),
    Column("summary", Text),
    Column("authors", JSON),
    Column("published_at", DateTime),
    Column("uri", String),
    Column("pdf_url", String),
    Column("minio_path", String, nullable=True),
    Column("pdf_status", String, default="pending"),
    Column("pdf_downloaded_at", DateTime, nullable=True),
    Column("pdf_size_bytes", BigInteger, nullable=True),
    Column("pdf_sha256", String, nullable=True),
    Column("rag_status", String, default="pending"),  # pending/chunked/embedded/failed
    Column("created_at", DateTime, server_default=func.now()), # pylint: disable=not-callable
    Column("updated_at", DateTime, onupdate=func.now()), # pylint: disable=not-callable
    schema='corpus'
)

chunk_table = Table(
    "chunk",
    metadata,
    Column("id", String, primary_key=True),
    Column("document_id", String, ForeignKey("corpus.document.id"), nullable=False),
    Column("chunk_index", Integer, nullable=False),
    Column("content", Text, nullable=False),
    Column("token_count", Integer),
    Column("embedding", Vector(EMBEDDING_DIM)),
    Column("section", String),
    Column("created_at", DateTime, server_default=func.now()), # pylint: disable=not-callable
    schema='corpus'
)