"""
Wrapper around the local all-MiniLM-L6-v2 embedding model.

Exposes two public functions:
  - embed(text)        : encode a single text → list[float] of dim 384
  - embed_batch(texts) : encode multiple texts → list[list[float]]

The model is loaded once (singleton via lru_cache) to avoid paying the
loading cost (~1-3s, ~100 MB of RAM) on every call.
"""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384          # output vector dimension for this model
DEFAULT_BATCH_SIZE = 32      # reasonable batch size for CPU inference

@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """
    Load the model once and keep it in memory.

    The lru_cache(maxsize=1) decorator ensures the SentenceTransformer is
    instantiated only on the first call. All subsequent calls return the same
    cached instance at near-zero cost.

    Returns:
        SentenceTransformer: the loaded model instance.
    """
    return SentenceTransformer(MODEL_NAME)

def embed_batch(
        texts: list[str],
        batch_size: int = DEFAULT_BATCH_SIZE,
        normalize: bool = True,
) -> list[list[float]]:
    """
    Encode a list of texts into embedding vectors.

    Much faster than calling embed() in a loop because the model processes
    texts in parallel (matrix parallelism on CPU/GPU).

    Args:
        texts: list of strings to encode.
        batch_size: number of texts processed simultaneously by the model.
                    32 is a good default on CPU.
        normalize: if True, normalizes vectors to unit norm.
                   Recommended: makes cosine similarity equivalent to dot
                   product, which is faster on vector databases.

    Returns:
        list[list[float]]: one 384-dim vector per input text, in the same
                           order as `texts`.
    """
    if not texts:
        return []

    model = _get_model()

    vectors = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=normalize,
        convert_to_numpy=True,
        show_progress_bar=True,
    )
    return vectors.tolist()

def embed(
        text: str,
        normalize: bool = True,
) -> list[float]:
    """
    Encode a single text into an embedding vector.

    Implemented as a thin wrapper around embed_batch to avoid logic
    duplication.

    Args:
        text: string to encode.
        normalize: see embed_batch.

    Returns:
        list[float] of length EMBEDDING_DIM (= 384).
    """
    return embed_batch([text], normalize=normalize)[0]
