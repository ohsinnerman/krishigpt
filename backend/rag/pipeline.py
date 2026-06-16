import os, hashlib, json
from typing import Optional

from langdetect import detect, LangDetectException

from rag.vector_store import load_index
from rag.retriever import retrieve
from rag.generator import generate
from data.pincode_mapper import get_region_from_pincode

CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TOP_K = int(os.getenv("RAG_TOP_K", "5"))

SUPPORTED_LANGS = {"en", "hi", "kn", "ta", "te", "mr", "gu", "pa"}


class KrishiGPTPipeline:
    def __init__(self):
        print("Loading FAISS index...")
        self.faiss_index, self.chunks = load_index()
        self.redis = None
        self._redis_tried = False
        # Warm up the embedding model at startup so the FIRST /chat request does
        # not race the (slow) lazy model download/load and 500.
        print("Warming up embedding model...")
        try:
            from rag.embeddings import embed_query
            embed_query("warmup")
        except Exception as e:
            print(f"WARNING: embedder warmup failed: {e}")
        print(f"Pipeline ready. {len(self.chunks)} chunks loaded.")

    async def _get_redis(self):
        if self.redis is None and not self._redis_tried:
            self._redis_tried = True
            try:
                import redis.asyncio as aioredis
                self.redis = aioredis.from_url(REDIS_URL, decode_responses=True)
            except Exception:
                self.redis = None
        return self.redis

    async def _cache_get(self, key: str) -> Optional[dict]:
        try:
            r = await self._get_redis()
            if r is None:
                return None
            val = await r.get(key)
            return json.loads(val) if val else None
        except Exception:
            return None  # degrade gracefully

    async def _cache_set(self, key: str, value: dict):
        try:
            r = await self._get_redis()
            if r is None:
                return
            await r.setex(key, CACHE_TTL, json.dumps(value))
        except Exception:
            pass  # non-fatal

    def _detect_language(self, text: str, hint: str = "en") -> str:
        if hint in SUPPORTED_LANGS:
            return hint
        try:
            detected = detect(text)
            return detected if detected in SUPPORTED_LANGS else "en"
        except LangDetectException:
            return "en"

    async def query(
        self,
        message: str,
        language: str = "en",
        pincode: Optional[str] = None,
        session_id: Optional[str] = None,
        region_filter: bool = True,  # Set False for ablation study
    ) -> dict:
        language = self._detect_language(message, hint=language)

        region_info = get_region_from_pincode(pincode) if pincode else None
        state = region_info.get("state") if region_info else None
        region_display = (
            f"{region_info['district']}, {region_info['state']}"
            if region_info else None
        )

        cache_key = "query:" + hashlib.sha256(
            f"{message}:{state or ''}:{language}:{region_filter}".encode()
        ).hexdigest()[:32]

        cached = await self._cache_get(cache_key)
        if cached:
            cached["cache_hit"] = True
            return cached

        retrieved = retrieve(
            query=message,
            faiss_index=self.faiss_index,
            chunks=self.chunks,
            state=state if region_filter else None,
            top_k=TOP_K,
        )

        response_text = await generate(
            question=message,
            context_chunks=retrieved,
            language=language,
            region=region_display,
        )

        result = {
            "response": response_text,
            "sources": [
                {
                    "title": c.get("source_title", "Unknown"),
                    "state": c.get("state", "pan-india"),
                    "topic": c.get("topic", "general"),
                    "score": round(c["score"], 3),
                }
                for c in retrieved
            ],
            "region": region_display,
            "language": language,
            "cache_hit": False,
        }

        await self._cache_set(cache_key, result)
        return result
