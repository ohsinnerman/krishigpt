# MASTER_PROMPT.md
# KrishiGPT — Complete Build Specification for Claude Code

> Paste this entire file into Claude Code at the start of your session.
> Every detail needed to build KrishiGPT is in this document.

---

## WHAT YOU ARE BUILDING

KrishiGPT is a region-aware multilingual RAG (Retrieval-Augmented Generation) agricultural advisor chatbot for Indian farmers. It answers farming questions in 7 Indic languages by retrieving from a curated corpus of ICAR agricultural documents, then synthesizing answers using Gemini 1.5 Flash. The core innovation is **region-prioritized retrieval**: every document chunk is tagged with state and agro-climatic zone, and the retriever boosts scores for chunks matching the farmer's pin code before sending context to the LLM.

---

## TECH STACK (DO NOT CHANGE THESE)

```
Backend:     FastAPI (Python 3.11), uvicorn
RAG:         LangChain (orchestration), FAISS-CPU (vector index), sentence-transformers
Embeddings:  paraphrase-multilingual-MiniLM-L12-v2 (384 dimensions)
Generator:   Google Gemini 1.5 Flash via google-generativeai SDK
Translation: Bhashini ULCA API (ASR, TTS, translation)
WhatsApp:    Twilio WhatsApp Business API
Frontend:    Next.js 14 (App Router), Tailwind CSS, shadcn/ui
Database:    PostgreSQL (sessions, messages), Redis (cache, rate limiting)
Infra:       Docker Compose
```

---

## COMPLETE DIRECTORY STRUCTURE

Build exactly this structure. Every file listed here must exist:

```
krishigpt/
├── backend/
│   ├── main.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── pipeline.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   └── generator.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── ingest.py
│   │   ├── chunker.py
│   │   ├── pincode_mapper.py
│   │   └── pincodes.csv          ← download from data.gov.in
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── whatsapp.py
│   │   └── bhashini.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── session.py
│   ├── tests/
│   │   ├── test_retrieval.py
│   │   ├── test_generation.py
│   │   └── conftest.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   ├── chat/
│   │   │   │   └── page.tsx
│   │   │   └── api/
│   │   │       └── chat/
│   │   │           └── route.ts
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── ChatBubble.tsx
│   │   │   ├── LanguageSelector.tsx
│   │   │   ├── PincodeInput.tsx
│   │   │   ├── SourceCard.tsx
│   │   │   └── VoiceButton.tsx
│   │   └── lib/
│   │       ├── api.ts
│   │       └── types.ts
│   ├── package.json
│   └── Dockerfile
├── scripts/
│   ├── download_corpus.sh
│   ├── build_index.py
│   ├── evaluate.py
│   └── create_eval_set.py
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## BACKEND — COMPLETE IMPLEMENTATION SPEC

### requirements.txt
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic==2.7.0
python-dotenv==1.0.1
google-generativeai==0.7.0
sentence-transformers==3.0.1
faiss-cpu==1.8.0
langchain==0.2.0
langchain-community==0.2.0
PyMuPDF==1.24.4
pytesseract==0.3.10
Pillow==10.3.0
langdetect==1.0.9
redis==5.0.4
sqlalchemy==2.0.30
asyncpg==0.29.0
twilio==9.1.0
httpx==0.27.0
slowapi==0.1.9
structlog==24.1.0
pytest==8.2.0
pytest-asyncio==0.23.7
numpy==1.26.4
pandas==2.2.2
```

---

### backend/main.py — COMPLETE IMPLEMENTATION

```python
import os, time, hashlib
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from rag.pipeline import KrishiGPTPipeline

limiter = Limiter(key_func=get_remote_address)
pipeline: KrishiGPTPipeline = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    pipeline = KrishiGPTPipeline()
    yield

app = FastAPI(title="KrishiGPT", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Models ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    language: str = "en"
    pincode: Optional[str] = None
    session_id: Optional[str] = None

class SourceDoc(BaseModel):
    title: str
    state: str
    topic: str
    score: float

class ChatResponse(BaseModel):
    response: str
    sources: list[SourceDoc]
    region: Optional[str]
    language: str
    latency_ms: int

# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(req: ChatRequest, request: Request):
    t0 = time.monotonic()
    try:
        result = await pipeline.query(
            message=req.message,
            language=req.language,
            pincode=req.pincode,
            session_id=req.session_id,
        )
        result["latency_ms"] = int((time.monotonic() - t0) * 1000)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "chunks_loaded": len(pipeline.chunks) if pipeline else 0,
        "model": "paraphrase-multilingual-MiniLM-L12-v2",
        "generator": "gemini-1.5-flash",
    }

@app.get("/languages")
async def languages():
    return {"supported": [
        {"code": "en", "name": "English", "native": "English"},
        {"code": "hi", "name": "Hindi", "native": "हिन्दी"},
        {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ"},
        {"code": "ta", "name": "Tamil", "native": "தமிழ்"},
        {"code": "te", "name": "Telugu", "native": "తెలుగు"},
        {"code": "mr", "name": "Marathi", "native": "मराठी"},
        {"code": "gu", "name": "Gujarati", "native": "ગુજરાતી"},
        {"code": "pa", "name": "Punjabi", "native": "ਪੰਜਾਬੀ"},
    ]}

@app.get("/pincode/{pincode}")
async def resolve_pincode(pincode: str):
    from data.pincode_mapper import get_region_from_pincode
    info = get_region_from_pincode(pincode)
    if not info:
        raise HTTPException(404, "Pincode not found")
    return info

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    from integrations.whatsapp import handle_whatsapp_message
    form_data = await request.form()
    return await handle_whatsapp_message(dict(form_data), pipeline)

@app.post("/feedback")
async def feedback(message_id: str, score: int):
    # score: 1 = helpful, -1 = not helpful
    # TODO: store in postgres
    return {"status": "recorded"}
```

---

### backend/rag/embeddings.py — COMPLETE IMPLEMENTATION

```python
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
        normalize_embeddings=True,  # L2 normalize → cosine sim = dot product
        convert_to_numpy=True,
    )
    return embeddings.astype(np.float32)

def embed_query(query: str) -> np.ndarray:
    """Embed a single query string. Returns shape (1, 384)."""
    return embed_texts([query])
```

---

### backend/rag/vector_store.py — COMPLETE IMPLEMENTATION

```python
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
        return np.array([[]] * 1), np.array([[-1]] * 1)
    k = min(top_k, index.ntotal)
    scores, indices = index.search(query_vec, k)
    return scores, indices
```

---

### backend/rag/retriever.py — COMPLETE IMPLEMENTATION

This is the core innovation. Read every line carefully.

```python
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
```

---

### backend/rag/generator.py — COMPLETE IMPLEMENTATION

```python
import os
import google.generativeai as genai
from typing import Optional

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
_model = genai.GenerativeModel("gemini-1.5-flash")

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi (हिन्दी)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "mr": "Marathi (मराठी)",
    "gu": "Gujarati (ગુજરાતી)",
    "pa": "Punjabi (ਪੰਜਾਬੀ)",
}

# Language-specific instruction (in the target language — forces correct output)
LANGUAGE_INSTRUCTIONS = {
    "en": "Respond in clear, simple English that a farmer can understand.",
    "hi": "केवल हिन्दी में जवाब दें। सरल शब्दों में लिखें जो एक किसान समझ सके। अंग्रेजी के शब्द कम से कम प्रयोग करें।",
    "kn": "ಕೇವಲ ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರ ನೀಡಿ. ರೈತರಿಗೆ ಅರ್ಥವಾಗುವ ಸರಳ ಭಾಷೆ ಬಳಸಿ. ಇಂಗ್ಲಿಷ್ ಪದಗಳನ್ನು ತಪ್ಪಿಸಿ.",
    "ta": "தமிழிலே மட்டும் பதில் சொல்லுங்கள். விவசாயிகளுக்கு புரியும் எளிய வார்த்தைகளை பயன்படுத்துங்கள்.",
    "te": "తెలుగులో మాత్రమే సమాధానం ఇవ్వండి. రైతులకు అర్థమయ్యే సాధారణ పదాలు వాడండి.",
    "mr": "केवल मराठीत उत्तर द्या. शेतकऱ्यांना समजेल अशा सोप्या भाषेत लिहा.",
    "gu": "ફક્ત ગુજરાતીમાં જ જવાબ આપો. ખેડૂતોને સમજાય તેવી સરળ ભાષા વાપરો.",
    "pa": "ਸਿਰਫ਼ ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦਿਓ। ਕਿਸਾਨਾਂ ਨੂੰ ਸਮਝ ਆਉਣ ਵਾਲੀ ਸਰਲ ਭਾਸ਼ਾ ਵਰਤੋ।",
}

# Terms that must NEVER be translated
PRESERVE_TERMS = "NPK, DAP, Urea, PMFBY, PMKISAN, KCC, pH, MSP, KVK, ICAR"

def build_prompt(
    question: str,
    context_chunks: list[dict],
    language: str,
    region: Optional[str],
) -> str:
    lang_name = LANGUAGE_NAMES.get(language, "English")
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["en"])
    region_context = f"The farmer is from {region}." if region else "The farmer's region is not specified."
    
    # Build context section
    if context_chunks:
        context_sections = []
        for i, chunk in enumerate(context_chunks, 1):
            context_sections.append(
                f"[Document {i}: {chunk.get('source_title', 'Unknown')}, "
                f"State: {chunk.get('state', 'pan-india')}]\n"
                f"{chunk['text']}"
            )
        context = "\n\n".join(context_sections)
    else:
        context = "No specific documents found in the knowledge base."
    
    prompt = f"""You are KrishiGPT, a trusted agricultural advisor for Indian farmers. You give practical, accurate advice based on official ICAR (Indian Council of Agricultural Research) documents.

REGIONAL CONTEXT: {region_context}

CRITICAL LANGUAGE INSTRUCTION: {lang_instruction}
These technical terms must NEVER be translated, always keep as-is: {PRESERVE_TERMS}

RETRIEVED AGRICULTURAL DOCUMENTS:
{context}

FARMER'S QUESTION: {question}

RESPONSE RULES:
1. Answer ONLY in {lang_name}. Not a single sentence in any other language.
2. Be practical and specific. A farmer should be able to act on your answer immediately.
3. For pest/disease questions: (a) Name what it is, (b) Give specific treatment with dosage from the documents, (c) Give one prevention tip.
4. For fertilizer questions: Give specific dose (kg/hectare or kg/acre), timing, and method of application.
5. For scheme questions (PMFBY/PMKISAN/KCC): State eligibility criteria, documents needed, and where to apply. Be PRECISE about dates and amounts — only state what is in the documents.
6. NEVER make up numbers, dosages, dates, or eligibility rules that are not in the retrieved documents.
7. If the documents don't contain the answer: Say "मुझे इस बारे में सटीक जानकारी नहीं है" (or equivalent in {lang_name}), then suggest contacting the local KVK.
8. End every response with ONE practical tip specific to {region or 'the farmer\'s region'}.
9. Keep response to 4-6 sentences maximum. Farmers need brevity.

RESPONSE IN {lang_name.upper()}:"""
    
    return prompt

async def generate(
    question: str,
    context_chunks: list[dict],
    language: str,
    region: Optional[str],
    max_tokens: int = 500,
) -> str:
    """Generate response using Gemini 1.5 Flash."""
    prompt = build_prompt(question, context_chunks, language, region)
    
    response = _model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.3,  # Low temperature = more factual, less hallucination
            top_p=0.8,
        ),
    )
    
    # Basic script validation
    text = response.text.strip()
    if language != "en" and not _has_correct_script(text, language):
        # Fallback: try once more with even stronger instruction
        stronger_prompt = f"IMPORTANT: Your ENTIRE response must be in {LANGUAGE_NAMES[language]} script only.\n\n" + prompt
        response = _model.generate_content(stronger_prompt)
        text = response.text.strip()
    
    return text

def _has_correct_script(text: str, lang: str) -> bool:
    """Check if text contains expected Unicode script characters."""
    SCRIPT_RANGES = {
        "hi": (0x0900, 0x097F), "mr": (0x0900, 0x097F),
        "kn": (0x0C80, 0x0CFF), "ta": (0x0B80, 0x0BFF),
        "te": (0x0C00, 0x0C7F), "gu": (0x0A80, 0x0AFF),
        "pa": (0x0A00, 0x0A7F),
    }
    if lang not in SCRIPT_RANGES:
        return True
    lo, hi = SCRIPT_RANGES[lang]
    script_chars = sum(1 for c in text if lo <= ord(c) <= hi)
    alpha_chars = sum(1 for c in text if c.isalpha())
    return alpha_chars > 0 and (script_chars / alpha_chars) > 0.25
```

---

### backend/rag/pipeline.py — COMPLETE IMPLEMENTATION

```python
import os, hashlib, json
from typing import Optional
import redis.asyncio as aioredis
from langdetect import detect, LangDetectException

from rag.embeddings import embed_query
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
        self.redis: Optional[aioredis.Redis] = None
        print(f"Pipeline ready. {len(self.chunks)} chunks loaded.")
    
    async def _get_redis(self) -> aioredis.Redis:
        if self.redis is None:
            self.redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        return self.redis
    
    async def _cache_get(self, key: str) -> Optional[dict]:
        try:
            r = await self._get_redis()
            val = await r.get(key)
            return json.loads(val) if val else None
        except Exception:
            return None  # Cache miss on error — degrade gracefully
    
    async def _cache_set(self, key: str, value: dict):
        try:
            r = await self._get_redis()
            await r.setex(key, CACHE_TTL, json.dumps(value))
        except Exception:
            pass  # Cache write failure is non-fatal
    
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
        # Detect/confirm language
        language = self._detect_language(message, hint=language)
        
        # Resolve region from pincode
        region_info = get_region_from_pincode(pincode) if pincode else None
        state = region_info.get("state") if region_info else None
        region_display = (
            f"{region_info['district']}, {region_info['state']}" 
            if region_info else None
        )
        
        # Cache key
        cache_key = "query:" + hashlib.sha256(
            f"{message}:{state or ''}:{language}".encode()
        ).hexdigest()[:32]
        
        # Cache check
        cached = await self._cache_get(cache_key)
        if cached:
            cached["cache_hit"] = True
            return cached
        
        # Retrieve
        retrieved = retrieve(
            query=message,
            faiss_index=self.faiss_index,
            chunks=self.chunks,
            state=state if region_filter else None,
            top_k=TOP_K,
        )
        
        # Generate
        response_text = await generate(
            question=message,
            context_chunks=retrieved,
            language=language,
            region=region_display,
        )
        
        # Build response
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
        
        # Cache and return
        await self._cache_set(cache_key, result)
        return result
```

---

### backend/data/pincode_mapper.py — COMPLETE IMPLEMENTATION

```python
import os
import csv
from functools import lru_cache
from typing import Optional

# Agro-climatic zone by state
AGRO_ZONES = {
    "Punjab": "IGP-Northwest", "Haryana": "IGP-Northwest",
    "Delhi": "IGP-Northwest", "Chandigarh": "IGP-Northwest",
    "Himachal Pradesh": "Western Himalaya",
    "Jammu and Kashmir": "Western Himalaya", "Ladakh": "Western Himalaya",
    "Uttarakhand": "Western Himalaya",
    "Uttar Pradesh": "IGP-Central",
    "Bihar": "IGP-East",
    "West Bengal": "Eastern", "Odisha": "Eastern",
    "Jharkhand": "Eastern", "Chhattisgarh": "Eastern",
    "Assam": "Northeast", "Meghalaya": "Northeast", "Manipur": "Northeast",
    "Nagaland": "Northeast", "Arunachal Pradesh": "Northeast",
    "Mizoram": "Northeast", "Tripura": "Northeast", "Sikkim": "Northeast",
    "Madhya Pradesh": "Central",
    "Maharashtra": "Deccan", "Goa": "South-Coastal",
    "Gujarat": "Arid-Semi", "Dadra and Nagar Haveli": "Arid-Semi",
    "Rajasthan": "Arid",
    "Karnataka": "Deccan-South",
    "Andhra Pradesh": "Deccan-South", "Telangana": "Deccan-South",
    "Tamil Nadu": "South", "Puducherry": "South",
    "Kerala": "South-Coastal", "Lakshadweep": "South-Coastal",
    "Andaman and Nicobar Islands": "Island",
}

# Fallback mapping: first 2 digits of pincode → approximate state
# This covers cases where pincodes.csv doesn't have a match
PINCODE_PREFIX_STATE = {
    "11": "Delhi", "12": "Haryana", "13": "Haryana", "14": "Punjab",
    "15": "Punjab", "16": "Punjab", "17": "Himachal Pradesh",
    "18": "Jammu and Kashmir", "19": "Jammu and Kashmir",
    "20": "Uttar Pradesh", "21": "Uttar Pradesh", "22": "Uttar Pradesh",
    "23": "Uttar Pradesh", "24": "Uttar Pradesh", "25": "Uttar Pradesh",
    "26": "Uttar Pradesh", "27": "Uttar Pradesh", "28": "Uttar Pradesh",
    "30": "Rajasthan", "31": "Rajasthan", "32": "Rajasthan",
    "33": "Rajasthan", "34": "Rajasthan",
    "36": "Gujarat", "37": "Gujarat", "38": "Gujarat", "39": "Gujarat",
    "40": "Maharashtra", "41": "Maharashtra", "42": "Maharashtra",
    "43": "Maharashtra", "44": "Maharashtra",
    "45": "Madhya Pradesh", "46": "Madhya Pradesh", "47": "Madhya Pradesh",
    "48": "Madhya Pradesh", "49": "Chhattisgarh",
    "50": "Telangana", "51": "Andhra Pradesh", "52": "Andhra Pradesh",
    "53": "Andhra Pradesh",
    "56": "Karnataka", "57": "Karnataka", "58": "Karnataka", "59": "Karnataka",
    "60": "Tamil Nadu", "61": "Tamil Nadu", "62": "Tamil Nadu",
    "63": "Tamil Nadu", "64": "Tamil Nadu",
    "67": "Kerala", "68": "Kerala", "69": "Kerala",
    "70": "West Bengal", "71": "West Bengal", "72": "West Bengal",
    "73": "West Bengal",
    "74": "West Bengal", "75": "Odisha", "76": "Odisha", "77": "Odisha",
    "78": "Assam", "79": "Assam",
    "80": "Bihar", "81": "Bihar", "82": "Bihar", "83": "Bihar", "84": "Bihar",
    "85": "Jharkhand",
}

_pincode_db: dict = {}
_loaded = False

def _load_pincode_db():
    global _pincode_db, _loaded
    if _loaded:
        return
    csv_path = os.getenv("PINCODE_DB_PATH", "data/pincodes.csv")
    if not os.path.exists(csv_path):
        print(f"WARNING: {csv_path} not found. Using prefix-only fallback.")
        _loaded = True
        return
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pin = row.get("pincode", row.get("Pincode", "")).strip()
            if pin:
                _pincode_db[pin] = {
                    "district": row.get("districtname", row.get("District", "Unknown")).strip(),
                    "state": row.get("statename", row.get("State", "Unknown")).strip(),
                    "division": row.get("divisionname", row.get("Division", "")).strip(),
                }
    print(f"Loaded {len(_pincode_db)} pincodes from {csv_path}")
    _loaded = True

@lru_cache(maxsize=10000)
def get_region_from_pincode(pincode: str) -> Optional[dict]:
    _load_pincode_db()
    
    pincode = pincode.strip()
    if not pincode.isdigit() or len(pincode) != 6:
        return None
    
    # Exact match
    if pincode in _pincode_db:
        info = _pincode_db[pincode]
        state = info["state"]
        return {
            "pincode": pincode,
            "district": info["district"],
            "state": state,
            "agro_zone": AGRO_ZONES.get(state, "Unknown"),
            "division": info.get("division", ""),
        }
    
    # Prefix fallback
    prefix = pincode[:2]
    state = PINCODE_PREFIX_STATE.get(prefix)
    if state:
        return {
            "pincode": pincode,
            "district": "Unknown",
            "state": state,
            "agro_zone": AGRO_ZONES.get(state, "Unknown"),
            "division": "",
        }
    
    return None
```

---

### backend/data/ingest.py — COMPLETE IMPLEMENTATION

```python
"""
Ingestion pipeline: PDF/HTML documents → text → chunks → embeddings → FAISS index.
Usage: python -m data.ingest --corpus-dir data/corpus --output-dir data
"""
import os, sys, argparse, re, uuid
import fitz  # PyMuPDF
from pathlib import Path
from langdetect import detect, LangDetectException
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.embeddings import embed_texts
from rag.vector_store import build_index, save_index

# ── Chunk parameters ─────────────────────────────────────────────────────────
CHUNK_SIZE = 512      # characters (approx 400 words)
CHUNK_OVERLAP = 64    # characters

# ── State / topic detection ───────────────────────────────────────────────────
STATE_KEYWORDS = {
    "karnataka": "Karnataka", "andhra": "Andhra Pradesh", "telangana": "Telangana",
    "tamilnadu": "Tamil Nadu", "kerala": "Kerala", "maharashtra": "Maharashtra",
    "gujarat": "Gujarat", "rajasthan": "Rajasthan", "punjab": "Punjab",
    "haryana": "Haryana", "uttarpradesh": "Uttar Pradesh", "madhyapradesh": "Madhya Pradesh",
    "westbengal": "West Bengal", "odisha": "Odisha", "assam": "Assam",
    "bihar": "Bihar", "jharkhand": "Jharkhand", "chhattisgarh": "Chhattisgarh",
    # Short codes
    "_kk_": "Karnataka", "_tn_": "Tamil Nadu", "_ap_": "Andhra Pradesh",
    "_ts_": "Telangana", "_mh_": "Maharashtra", "_gj_": "Gujarat",
    "_pb_": "Punjab", "_hr_": "Haryana", "_up_": "Uttar Pradesh",
    "_mp_": "Madhya Pradesh", "_wb_": "West Bengal", "_od_": "Odisha",
}

TOPIC_KEYWORDS = {
    "pest": ["pest", "insect", "aphid", "thrips", "borer", "whitefly", "mite", "weevil"],
    "disease": ["disease", "blight", "rust", "wilt", "rot", "fungal", "bacterial", "virus", "blast"],
    "fertilizer": ["fertilizer", "nutrient", "nitrogen", "phosphorus", "urea", "DAP", "potassium", "manure"],
    "irrigation": ["irrigation", "water management", "drip", "sprinkler", "flood irrigation"],
    "harvest": ["harvest", "harvesting", "yield", "storage", "post-harvest", "threshing"],
    "variety": ["variety", "cultivar", "hybrid", "seed selection", "sowing"],
    "scheme": ["PMFBY", "PMKISAN", "KCC", "insurance", "credit", "loan", "subsidy"],
    "soil": ["soil", "pH", "organic matter", "soil health", "drainage"],
}

AGRO_ZONES = {
    "Punjab": "IGP-Northwest", "Haryana": "IGP-Northwest", "Uttar Pradesh": "IGP-Central",
    "Bihar": "IGP-East", "West Bengal": "Eastern", "Odisha": "Eastern",
    "Assam": "Northeast", "Madhya Pradesh": "Central", "Maharashtra": "Deccan",
    "Gujarat": "Arid-Semi", "Rajasthan": "Arid", "Karnataka": "Deccan-South",
    "Andhra Pradesh": "Deccan-South", "Telangana": "Deccan-South",
    "Tamil Nadu": "South", "Kerala": "South-Coastal",
}

# ── Text extraction ────────────────────────────────────────────────────────────

def extract_text_from_pdf(path: str) -> str:
    doc = fitz.open(path)
    pages = []
    for page in doc:
        text = page.get_text("text")
        if len(text.strip()) < 50:
            # Low text density → OCR (requires tesseract installed)
            try:
                import pytesseract
                from PIL import Image
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img, lang="eng")
            except Exception:
                pass
        pages.append(text)
    return "\n\n".join(pages)

def extract_text_from_html(path: str) -> str:
    from html.parser import HTMLParser
    class TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.texts = []
            self._skip = False
        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style", "nav", "footer"):
                self._skip = True
        def handle_endtag(self, tag):
            if tag in ("script", "style", "nav", "footer"):
                self._skip = False
        def handle_data(self, data):
            if not self._skip:
                self.texts.append(data)
    
    with open(path, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    parser = TextExtractor()
    parser.feed(content)
    return " ".join(parser.texts)

# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    # Clean
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()
    
    if len(text) <= chunk_size:
        return [text] if len(text) > 100 else []
    
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        
        # Try to break at paragraph
        if end < len(text):
            for sep in ["\n\n", "\n", ". ", " "]:
                pos = text.rfind(sep, start + chunk_size // 2, end)
                if pos != -1:
                    end = pos + len(sep)
                    break
        
        chunk = text[start:end].strip()
        if len(chunk) >= 100:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text) - 100:
            break
    
    return chunks

# ── Metadata tagging ──────────────────────────────────────────────────────────

def detect_state(filename: str, text: str) -> str:
    fn_lower = filename.lower().replace(" ", "").replace("-", "").replace("_", "")
    for keyword, state in STATE_KEYWORDS.items():
        if keyword.strip("_") in fn_lower:
            return state
    text_lower = text[:500].lower()
    for keyword, state in STATE_KEYWORDS.items():
        if keyword.strip("_") in text_lower:
            return state
    return "pan-india"

def detect_topic(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        scores[topic] = sum(1 for kw in keywords if kw.lower() in text_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"

def detect_language(text: str) -> str:
    try:
        return detect(text[:200])
    except LangDetectException:
        return "en"

def detect_crop(filename: str, text: str) -> str | None:
    CROPS = ["paddy", "rice", "wheat", "cotton", "sugarcane", "groundnut",
             "soybean", "maize", "corn", "tomato", "potato", "onion",
             "banana", "mango", "grape", "turmeric", "ginger", "pulses",
             "tur", "moong", "urad", "chana", "mustard", "sunflower"]
    combined = (filename + " " + text[:300]).lower()
    for crop in CROPS:
        if crop in combined:
            return crop
    return None

# ── Main ingestion ────────────────────────────────────────────────────────────

def ingest_file(filepath: str) -> list[dict]:
    path = Path(filepath)
    ext = path.suffix.lower()
    
    if ext == ".pdf":
        text = extract_text_from_pdf(filepath)
    elif ext in (".html", ".htm"):
        text = extract_text_from_html(filepath)
    else:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    
    if len(text.strip()) < 200:
        print(f"  SKIP (too short): {path.name}")
        return []
    
    # Detect metadata
    state = detect_state(path.name, text)
    topic = detect_topic(text)
    language = detect_language(text)
    crop = detect_crop(path.name, text)
    agro_zone = AGRO_ZONES.get(state, "pan-india")
    
    # Extract title from first line or filename
    first_line = text.split("\n")[0][:100].strip()
    title = first_line if len(first_line) > 10 else path.stem.replace("_", " ").title()
    
    # Chunk
    raw_chunks = chunk_text(text)
    
    chunks = []
    for i, chunk_text_val in enumerate(raw_chunks):
        chunks.append({
            "chunk_id": str(uuid.uuid4()),
            "source_file": path.name,
            "source_title": title,
            "state": state,
            "agro_zone": agro_zone,
            "crop": crop,
            "topic": topic,
            "language": language,
            "chunk_index": i,
            "text": chunk_text_val,
        })
    
    print(f"  {path.name}: {len(chunks)} chunks, state={state}, topic={topic}")
    return chunks

def run_ingestion(corpus_dir: str, output_dir: str):
    corpus_path = Path(corpus_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    EXTENSIONS = {".pdf", ".html", ".htm", ".txt"}
    files = [f for f in corpus_path.rglob("*") if f.suffix.lower() in EXTENSIONS]
    
    print(f"Found {len(files)} files to ingest.")
    
    all_chunks = []
    for f in files:
        chunks = ingest_file(str(f))
        all_chunks.extend(chunks)
    
    if not all_chunks:
        print("ERROR: No chunks produced. Check corpus directory and file formats.")
        return
    
    print(f"\nTotal chunks: {len(all_chunks)}")
    print("Embedding... (this takes a few minutes)")
    
    texts = [c["text"] for c in all_chunks]
    embeddings = embed_texts(texts)
    
    index = build_index(embeddings)
    save_index(index, all_chunks)
    
    print(f"\nDone! Index saved to {output_dir}/faiss.index")
    print(f"State distribution:")
    from collections import Counter
    states = Counter(c["state"] for c in all_chunks)
    for state, count in states.most_common(10):
        print(f"  {state}: {count} chunks")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", default="data/corpus")
    parser.add_argument("--output-dir", default="data")
    args = parser.parse_args()
    run_ingestion(args.corpus_dir, args.output_dir)
```

---

### backend/integrations/whatsapp.py — COMPLETE IMPLEMENTATION

```python
import os, hashlib, hmac, base64
from fastapi import HTTPException
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
import httpx

TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")

ONBOARDING_MSG = {
    "en": "Welcome to KrishiGPT 🌾 I answer farming questions in 7 languages.\nReply with your language:\n1=English\n2=हिन्दी\n3=ಕನ್ನಡ\n4=தமிழ்\n5=తెలుగు\n6=मराठी\n7=ਪੰਜਾਬੀ",
}
LANG_MAP = {"1": "en", "2": "hi", "3": "kn", "4": "ta", "5": "te", "6": "mr", "7": "pa"}

PINCODE_PROMPT = {
    "en": "Please send your 6-digit PIN code so I can give you region-specific advice.",
    "hi": "कृपया अपना 6 अंकों का पिन कोड भेजें ताकि मैं आपके क्षेत्र के अनुसार सलाह दे सकूं।",
    "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ 6 ಅಂಕಿಯ ಪಿನ್ ಕೋಡ್ ಕಳಿಸಿ ಇದರಿಂದ ನಿಮ್ಮ ಪ್ರದೇಶಕ್ಕೆ ಸೂಕ್ತ ಸಲಹೆ ನೀಡಲು ಅನುಕೂಲವಾಗುತ್ತದೆ.",
    "ta": "உங்கள் 6 இலக்க பின் கோடை அனுப்புங்கள் - உங்கள் பகுதிக்கு ஏற்ற ஆலோசனை தர உதவும்.",
    "te": "మీ 6-అంకెల పిన్ కోడ్ పంపండి - మీ ప్రాంతానికి తగిన సలహా ఇవ్వడానికి.",
    "mr": "कृपया तुमचा 6-अंकी पिन कोड पाठवा म्हणजे तुमच्या क्षेत्राला योग्य सल्ला देता येईल.",
    "gu": "કૃપા કરીને તમારો 6-અંક PIN કોડ મોકલો - તમારા વિસ્તારને અનુરૂપ સલાહ આપવા.",
    "pa": "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣਾ 6-ਅੰਕ ਦਾ ਪਿਨ ਕੋਡ ਭੇਜੋ - ਤੁਹਾਡੇ ਖੇਤਰ ਲਈ ਸਲਾਹ ਦੇਣ ਲਈ।",
}

# In-memory session store (replace with Redis in production)
_sessions = {}

async def handle_whatsapp_message(form_data: dict, pipeline) -> Response:
    from_number = form_data.get("From", "")
    body = form_data.get("Body", "").strip()
    num_media = int(form_data.get("NumMedia", 0))
    
    phone_hash = hashlib.sha256(from_number.encode()).hexdigest()[:16]
    session = _sessions.get(phone_hash, {})
    
    resp = MessagingResponse()
    
    # ── Handle voice note ─────────────────────────────────────────────────────
    if num_media > 0 and not body:
        media_url = form_data.get("MediaUrl0", "")
        media_type = form_data.get("MediaContentType0", "")
        if "audio" in media_type:
            body = await _transcribe_audio(media_url, session.get("language", "hi"))
            if not body:
                resp.message("Sorry, I couldn't understand the audio. Please type your question.")
                return Response(content=str(resp), media_type="text/xml")
    
    # ── Onboarding flow ───────────────────────────────────────────────────────
    if "language" not in session:
        if body in LANG_MAP:
            session["language"] = LANG_MAP[body]
            _sessions[phone_hash] = session
            resp.message(PINCODE_PROMPT.get(session["language"], PINCODE_PROMPT["en"]))
        else:
            resp.message(ONBOARDING_MSG["en"])
        return Response(content=str(resp), media_type="text/xml")
    
    if "pincode" not in session:
        if body.isdigit() and len(body) == 6:
            session["pincode"] = body
            _sessions[phone_hash] = session
            lang = session["language"]
            confirm = {
                "en": f"Got it! Pincode {body} set. Now ask me anything about farming! 🌾",
                "hi": f"ठीक है! पिन कोड {body} सेट हो गया। अब खेती के बारे में कोई भी सवाल पूछें! 🌾",
                "kn": f"ಸರಿ! ಪಿನ್ ಕೋಡ್ {body} ಸೆಟ್ ಆಗಿದೆ. ಈಗ ಕೃಷಿಯ ಬಗ್ಗೆ ಯಾವ ಪ್ರಶ್ನೆಯನ್ನಾದರೂ ಕೇಳಿ! 🌾",
            }
            resp.message(confirm.get(lang, confirm["en"]))
        else:
            resp.message("Please send a valid 6-digit PIN code.")
        return Response(content=str(resp), media_type="text/xml")
    
    # ── Normal query ──────────────────────────────────────────────────────────
    try:
        result = await pipeline.query(
            message=body,
            language=session["language"],
            pincode=session.get("pincode"),
        )
        reply = result["response"]
        if result.get("sources"):
            top_source = result["sources"][0]
            reply += f"\n\n📄 Source: {top_source['title']} ({top_source['state']})"
    except Exception as e:
        reply = "Sorry, I'm having trouble right now. Please try again in a moment."
    
    resp.message(reply)
    return Response(content=str(resp), media_type="text/xml")

async def _transcribe_audio(media_url: str, language: str) -> str | None:
    """Transcribe audio using Bhashini ASR."""
    from integrations.bhashini import transcribe_audio
    try:
        audio_data = await _download_audio(media_url)
        if audio_data:
            return await transcribe_audio(audio_data, language)
    except Exception as e:
        print(f"ASR error: {e}")
    return None

async def _download_audio(url: str) -> bytes | None:
    try:
        auth = (os.getenv("TWILIO_ACCOUNT_SID", ""), os.getenv("TWILIO_AUTH_TOKEN", ""))
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, auth=auth, timeout=10)
            return resp.content if resp.status_code == 200 else None
    except Exception:
        return None
```

---

### backend/integrations/bhashini.py — COMPLETE IMPLEMENTATION

```python
import os, base64
import httpx

BHASHINI_USER_ID = os.getenv("BHASHINI_USER_ID", "")
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY", "")
BHASHINI_BASE_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

BHASHINI_LANG_CODES = {
    "en": "en", "hi": "hi", "kn": "kn", "ta": "ta",
    "te": "te", "mr": "mr", "gu": "gu", "pa": "pa",
}

async def transcribe_audio(audio_bytes: bytes, language: str) -> str | None:
    """Convert audio bytes to text using Bhashini ASR."""
    if not BHASHINI_USER_ID or not BHASHINI_API_KEY:
        return None
    
    audio_b64 = base64.b64encode(audio_bytes).decode()
    lang_code = BHASHINI_LANG_CODES.get(language, "hi")
    
    payload = {
        "pipelineTasks": [{
            "taskType": "asr",
            "config": {
                "language": {"sourceLanguage": lang_code},
                "audioFormat": "ogg",
                "samplingRate": 16000,
            }
        }],
        "inputData": {
            "audio": [{"audioContent": audio_b64}]
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                BHASHINI_BASE_URL,
                json=payload,
                headers={
                    "userID": BHASHINI_USER_ID,
                    "ulcaApiKey": BHASHINI_API_KEY,
                    "Content-Type": "application/json",
                }
            )
            data = resp.json()
            return data["pipelineResponse"][0]["output"][0]["source"]
    except Exception as e:
        print(f"Bhashini ASR error: {e}")
        return None

async def translate_text(text: str, source_lang: str, target_lang: str) -> str | None:
    """Translate text using Bhashini IndicTrans2."""
    if source_lang == target_lang:
        return text
    if not BHASHINI_USER_ID or not BHASHINI_API_KEY:
        return None
    
    payload = {
        "pipelineTasks": [{
            "taskType": "translation",
            "config": {
                "language": {
                    "sourceLanguage": BHASHINI_LANG_CODES.get(source_lang, "en"),
                    "targetLanguage": BHASHINI_LANG_CODES.get(target_lang, "hi"),
                }
            }
        }],
        "inputData": {
            "input": [{"source": text}]
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                BHASHINI_BASE_URL,
                json=payload,
                headers={
                    "userID": BHASHINI_USER_ID,
                    "ulcaApiKey": BHASHINI_API_KEY,
                    "Content-Type": "application/json",
                }
            )
            data = resp.json()
            return data["pipelineResponse"][0]["output"][0]["target"]
    except Exception as e:
        print(f"Bhashini translation error: {e}")
        return None

async def synthesize_speech(text: str, language: str) -> bytes | None:
    """Convert text to speech using Bhashini TTS. Returns WAV bytes."""
    if not BHASHINI_USER_ID or not BHASHINI_API_KEY:
        return None
    
    lang_code = BHASHINI_LANG_CODES.get(language, "hi")
    
    payload = {
        "pipelineTasks": [{
            "taskType": "tts",
            "config": {
                "language": {"sourceLanguage": lang_code},
                "gender": "female",
                "samplingRate": 8000,
            }
        }],
        "inputData": {
            "input": [{"source": text}]
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                BHASHINI_BASE_URL,
                json=payload,
                headers={
                    "userID": BHASHINI_USER_ID,
                    "ulcaApiKey": BHASHINI_API_KEY,
                    "Content-Type": "application/json",
                }
            )
            data = resp.json()
            audio_b64 = data["pipelineResponse"][0]["audio"][0]["audioContent"]
            return base64.b64decode(audio_b64)
    except Exception as e:
        print(f"Bhashini TTS error: {e}")
        return None
```

---

## FRONTEND — IMPLEMENTATION SPEC

### frontend/src/lib/types.ts

```typescript
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceDoc[];
  region?: string;
  language: string;
  latency_ms?: number;
  timestamp: Date;
}

export interface SourceDoc {
  title: string;
  state: string;
  topic: string;
  score: number;
}

export interface Language {
  code: string;
  name: string;
  native: string;
}

export interface RegionInfo {
  pincode: string;
  district: string;
  state: string;
  agro_zone: string;
}
```

### frontend/src/lib/api.ts

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendChat(params: {
  message: string;
  language: string;
  pincode?: string;
  sessionId?: string;
}) {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: params.message,
      language: params.language,
      pincode: params.pincode,
      session_id: params.sessionId,
    }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function resolvePin(pincode: string) {
  const res = await fetch(`${API_URL}/pincode/${pincode}`);
  if (!res.ok) return null;
  return res.json();
}

export async function getLanguages() {
  const res = await fetch(`${API_URL}/languages`);
  return res.json();
}
```

### frontend/src/app/chat/page.tsx — KEY BEHAVIORS

The chat page must:
1. Show a header with: KrishiGPT logo, LanguageSelector, PincodeInput
2. Show a scrollable chat window with messages
3. Show a text input at the bottom with Send button
4. On send: add user message immediately, show typing indicator, then add assistant message
5. Each assistant message has a collapsible "Sources" section at the bottom
6. Language selection updates `language` state — all subsequent queries use new language
7. Pincode input shows resolved region below input (e.g., "📍 Bengaluru, Karnataka")
8. Example questions shown when chat is empty: click to auto-fill input

### Example questions to show (use these exactly):

```typescript
const EXAMPLE_QUESTIONS = {
  en: [
    "How do I control stem borer in paddy?",
    "What is the urea dose for wheat per acre?",
    "How do I apply for PMFBY crop insurance?",
  ],
  hi: [
    "धान में काण्ड कीट कैसे नियंत्रित करें?",
    "गेहूं में प्रति एकड़ यूरिया की मात्रा क्या है?",
    "PMFBY फसल बीमा के लिए कैसे आवेदन करें?",
  ],
  kn: [
    "ಭತ್ತದಲ್ಲಿ ಕಾಂಡ ಕೊರೆಯುವ ಹುಳ ಹೇಗೆ ನಿಯಂತ್ರಿಸುವುದು?",
    "ಗೋಧಿಗೆ ಪ್ರತಿ ಎಕರೆ ಯೂರಿಯಾ ಪ್ರಮಾಣ ಎಷ್ಟು?",
    "PMFBY ಬೆಳೆ ವಿಮೆಗೆ ಹೇಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು?",
  ],
  // Add for all 7 languages
};
```

---

## DOCKER COMPOSE — COMPLETE FILE

```yaml
version: "3.9"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./backend/data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: krishigpt
      POSTGRES_USER: krishigpt
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-localdev}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U krishigpt"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
  redisdata:
```

---

## SCRIPTS

### scripts/build_index.py

```python
#!/usr/bin/env python3
"""Run this once after downloading corpus to build the FAISS index."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from data.ingest import run_ingestion

if __name__ == "__main__":
    run_ingestion(
        corpus_dir="backend/data/corpus",
        output_dir="backend/data",
    )
```

### scripts/download_corpus.sh

Download at minimum these URLs for a working demo:

```bash
#!/bin/bash
set -e
mkdir -p backend/data/corpus

# TNAU Agritech (excellent structured content)
TNAU="https://agritech.tnau.ac.in"
wget -q "$TNAU/agriculture/agri_cereals_paddy.html" -O backend/data/corpus/paddy_tnau_en.html
wget -q "$TNAU/agriculture/agri_cereals_wheat.html" -O backend/data/corpus/wheat_tnau_en.html
wget -q "$TNAU/agriculture/agri_oilseeds_groundnut.html" -O backend/data/corpus/groundnut_tnau_en.html
wget -q "$TNAU/plant_protection/pp_fieldcrops_paddy_pest.html" -O backend/data/corpus/paddy_pest_tnau_en.html
wget -q "$TNAU/agriculture/agri_vegetables_tomato.html" -O backend/data/corpus/tomato_tnau_en.html
wget -q "$TNAU/agriculture/agri_vegetables_onion.html" -O backend/data/corpus/onion_tnau_en.html
wget -q "$TNAU/agriculture/agri_vegetables_cotton.html" -O backend/data/corpus/cotton_tnau_en.html

# Download India pincode DB
wget -q "https://raw.githubusercontent.com/sveltekit-india/pincode-data/main/pincodes.csv" \
  -O backend/data/pincodes.csv || \
wget -q "https://raw.githubusercontent.com/uohzxela/india-pincodes/master/data.csv" \
  -O backend/data/pincodes.csv

echo "Corpus downloaded to backend/data/corpus/"
echo "Pincode DB at backend/data/pincodes.csv"
echo ""
echo "Next step: python scripts/build_index.py"
```

---

## ENVIRONMENT FILE

```bash
# .env.example — copy to .env and fill in values

# REQUIRED — get from https://aistudio.google.com/
GOOGLE_API_KEY=

# REQUIRED — get from https://bhashini.gov.in/
BHASHINI_USER_ID=
BHASHINI_API_KEY=

# OPTIONAL — for WhatsApp integration
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Database
DATABASE_URL=postgresql://krishigpt:localdev@localhost:5432/krishigpt
REDIS_URL=redis://localhost:6379/0
POSTGRES_PASSWORD=localdev

# RAG Config
RAG_TOP_K=5
REGION_BOOST_EXACT=0.20
REGION_BOOST_ZONE=0.10
REGION_BOOST_PAN_INDIA=0.05
CACHE_TTL_SECONDS=3600
SESSION_TTL_HOURS=24
RATE_LIMIT_PER_MINUTE=10
MAX_TOKENS_OUTPUT=500

# Model Config
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
FAISS_INDEX_PATH=data/faiss.index
CHUNKS_PATH=data/chunks.pkl
PINCODE_DB_PATH=data/pincodes.csv

ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## CRITICAL IMPLEMENTATION RULES

1. **The FAISS retriever must always over-fetch (top_k × 4) before re-ranking.** If you don't over-fetch, you miss regional documents that would score higher after the boost.

2. **The system prompt language instruction must be IN the target language** (not just "respond in Hindi"). The Devanagari/Kannada/Tamil instruction text forces Gemini to pattern-match to that script.

3. **Never log full query text** — it may contain personal farming info. Log query_hash only.

4. **The pincode mapper must have a fallback** — not all pincodes will be in the CSV. The prefix fallback (first 2 digits → state) must always work.

5. **Cache must be non-blocking** — if Redis is down, the system still works. Wrap all Redis calls in try/except.

6. **The `region_filter` parameter in pipeline.query() must be toggleable** for the ablation study. Build it in from the start.

7. **Script validation is mandatory** — after generation, check that the response actually contains the right Unicode script. Gemini occasionally responds in English even when asked for regional language. If script check fails, retry once with a stronger prompt.

8. **WhatsApp webhook must return valid TwiML within 5 seconds** — Twilio times out at 15 seconds but LLM calls can take 4-8 seconds. Use streaming or ensure Gemini call completes < 10s.

9. **FAISS IndexFlatIP requires normalized vectors** — always use `normalize_embeddings=True` in SentenceTransformer. Without this, inner product ≠ cosine similarity and scores are meaningless.

10. **The chunker must include section headers in chunks** — when you encounter a header line (short line in ALL CAPS or title case followed by body text), include it at the start of the next chunk. This preserves context ("Under Application of Nitrogen: Use 120 kg/ha..." is only useful if you know it's about nitrogen).

---

## HOW TO START CLAUDE CODE SESSION

Paste this entire file at the start. Then say:

"Build KrishiGPT exactly as specified in this document. Start with the project scaffold, then ingestion pipeline, then RAG pipeline, then frontend, then WhatsApp. After each major component, run the tests specified in PIPELINE.md and confirm they pass before moving on. Ask me for API keys when you need them."
