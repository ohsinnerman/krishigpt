import os
import numpy as np
from sentence_transformers import SentenceTransformer

_model = None


def get_embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        model_name = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        _model = SentenceTransformer(model_name)
    return _model


def embed_texts(texts: list[str], batch_size: int = 64) -> np.ndarray:
    """
    Embed a list of texts. Returns normalized numpy array of shape (N, 384).
    Normalization enables cosine similarity via inner product.
    """
    model = get_embedder()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 100,
        normalize_embeddings=True,  # L2 normalize -> cosine sim = dot product
        convert_to_numpy=True,
    )
    return embeddings.astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string. Returns shape (1, 384)."""
    return embed_texts([query])
