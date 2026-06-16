import os, pickle
import faiss
import numpy as np
from typing import Optional

FAISS_PATH = os.getenv("FAISS_INDEX_PATH", "data/faiss.index")
CHUNKS_PATH = os.getenv("CHUNKS_PATH", "data/chunks.pkl")
EMBEDDING_DIM = 384


def build_index(embeddings: np.ndarray) -> faiss.Index:
    """Create FAISS IndexFlatIP index from normalized embeddings."""
    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    index.add(embeddings)
    return index


def save_index(index: faiss.Index, chunks: list[dict]):
    os.makedirs(os.path.dirname(FAISS_PATH) or ".", exist_ok=True)
    faiss.write_index(index, FAISS_PATH)
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)
    print(f"Saved index with {index.ntotal} vectors and {len(chunks)} chunks.")


def load_index() -> tuple[Optional[faiss.Index], list[dict]]:
    if not os.path.exists(FAISS_PATH) or not os.path.exists(CHUNKS_PATH):
        print("WARNING: No FAISS index found. Run scripts/build_index.py first.")
        return None, []
    index = faiss.read_index(FAISS_PATH)
    with open(CHUNKS_PATH, "rb") as f:
        chunks = pickle.load(f)
    print(f"Loaded index: {index.ntotal} vectors, {len(chunks)} chunks.")
    return index, chunks


def search(index: faiss.Index, query_vec: np.ndarray, top_k: int = 20) -> tuple[np.ndarray, np.ndarray]:
    """Returns (scores, indices) arrays of shape (1, top_k)."""
    if index is None or index.ntotal == 0:
        return np.array([[]]), np.array([[-1]])
    k = min(top_k, index.ntotal)
    scores, indices = index.search(query_vec, k)
    return scores, indices
