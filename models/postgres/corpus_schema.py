from sqlalchemy import Table, Column, String, Text, DateTime, MetaData, JSON

metadata = MetaData()

document_table = Table(
    "document",
    metadata,
    Column("id", String, primary_key=True), # L'URL arXiv sert d'ID unique
    Column("title", String, nullable=False),
    Column("summary", Text),
    Column("published", DateTime),
    Column("updated", DateTime),
    Column("authors", JSON), # Stocke la liste ['Author 1', 'Author 2']
    Column("pdf_url", String),
    Column("source", String)
)