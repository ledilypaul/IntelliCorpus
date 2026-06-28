"""fix chunk embedding dimension to 384

Revision ID: 25e9ba0767b4
Revises: e3117203a25a
Create Date: 2026-06-21 22:41:48.980977

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25e9ba0767b4'
down_revision: Union[str, Sequence[str], None] = 'e3117203a25a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # chunk.embedding was created as vector(1536) (OpenAI dims) but the
    # project uses sentence-transformers/all-MiniLM-L6-v2 (384 dims).
    # Table is empty (inserts were failing on the dimension mismatch), so a
    # plain type change is safe here. The HNSW index is tied to the column's
    # dimension, so it must be dropped and recreated.
    op.execute("DROP INDEX IF EXISTS corpus.chunk_embedding_hnsw_idx")
    op.execute("ALTER TABLE corpus.chunk ALTER COLUMN embedding TYPE vector(384)")
    op.execute("""
        CREATE INDEX IF NOT EXISTS chunk_embedding_hnsw_idx
        ON corpus.chunk USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS corpus.chunk_embedding_hnsw_idx")
    op.execute("ALTER TABLE corpus.chunk ALTER COLUMN embedding TYPE vector(1536)")
    op.execute("""
        CREATE INDEX IF NOT EXISTS chunk_embedding_hnsw_idx
        ON corpus.chunk USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
