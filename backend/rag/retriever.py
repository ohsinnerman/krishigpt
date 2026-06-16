import os
from typing import Optional
from rag.embeddings import embed_query
from rag.vector_store import search

# Boost weights — tune these based on eval results
BOOST_EXACT_STATE = float(os.getenv("REGION_BOOST_EXACT", "0.20"))
BOOST_SAME_ZONE = float(os.getenv("REGION_BOOST_ZONE", "0.10"))
BOOST_PAN_INDIA = float(os.getenv("REGION_BOOST_PAN_INDIA", "0.05"))

# Agro-climatic zone mapping
AGRO_ZONES = {
    "Punjab": "IGP-Northwest", "Haryana": "IGP-Northwest",
    "Uttar Pradesh": "IGP-Central", "Bihar": "IGP-East",
    "West Bengal": "Eastern", "Odisha": "Eastern", "Jharkhand": "Eastern",
    "Chhattisgarh": "Eastern", "Assam": "Northeast",
    "Madhya Pradesh": "Central", "Maharashtra": "Deccan",
    "Gujarat": "Arid-Semi", "Rajasthan": "Arid",
    "Karnataka": "Deccan-South", "Andhra Pradesh": "Deccan-South",
    "Telangana": "Deccan-South", "Tamil Nadu": "South",
    "Kerala": "South-Coastal", "Goa": "South-Coastal",
    "Himachal Pradesh": "Western Himalaya",
    "Uttarakhand": "Western Himalaya",
    "Delhi": "IGP-Northwest",
}


def retrieve(
    query: str,
    faiss_index,
    chunks: list[dict],
    state: Optional[str] = None,
    top_k: int = 5,
    candidate_multiplier: int = 4,
) -> list[dict]:
    """
    Region-aware retrieval.

    1. Embed query
    2. FAISS search for top (top_k * candidate_multiplier) candidates
    3. Apply region-aware score boosts
    4. Re-rank and return top_k

    Returns list of chunk dicts with added 'score' key.
    """
    if not chunks:
        return []

    # Step 1: Embed query
    query_vec = embed_query(query)  # shape (1, 384)

    # Step 2: FAISS search — over-fetch for re-ranking
    n_candidates = min(top_k * candidate_multiplier, len(chunks))
    scores, indices = search(faiss_index, query_vec, top_k=n_candidates)

    # Step 3: Region-aware re-ranking
    target_zone = AGRO_ZONES.get(state) if state else None
    candidates = []

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        chunk = chunks[int(idx)]
        chunk_state = chunk.get("state", "pan-india")
        chunk_zone = chunk.get("agro_zone", "")

        boost = 0.0
        region_match = "none"

        if state and chunk_state.lower() == state.lower():
            boost = BOOST_EXACT_STATE
            region_match = "exact_state"
        elif target_zone and chunk_zone == target_zone:
            boost = BOOST_SAME_ZONE
            region_match = "same_zone"
        elif chunk_state == "pan-india":
            boost = BOOST_PAN_INDIA
            region_match = "pan_india"

        candidates.append({
            **chunk,
            "score": float(score) + boost,
            "base_score": float(score),
            "region_match": region_match,
        })

    # Step 4: Re-rank by boosted score
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_k]
