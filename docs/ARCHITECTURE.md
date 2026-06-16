# KrishiGPT — System Architecture

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INGESTION PIPELINE                       │
│                                                                   │
│  ICAR PDFs ──┐                                                   │
│  KVK Books ──┤──► PyMuPDF ──► Chunker ──► Tagger ──► FAISS     │
│  Scheme Docs ┘      │                        │                   │
│                      │                  (state, zone,            │
│                   OCR fallback          crop, topic)             │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         INFERENCE PATH                           │
│                                                                   │
│  WhatsApp ──► Twilio webhook ──┐                                 │
│                                 ├──► FastAPI                     │
│  Web/Mobile ──► Next.js ────────┘       │                       │
│                                          ▼                       │
│                              Pincode Resolver                    │
│                                    │                             │
│                                    ▼                             │
│                           Region-Aware Retriever                 │
│                           (FAISS + metadata filter)              │
│                                    │                             │
│                                    ▼                             │
│                           Gemini 1.5 Flash                       │
│                           (prompt + context)                     │
│                                    │                             │
│                                    ▼                             │
│                           Bhashini IndicTrans2                   │
│                           (if target ≠ English)                  │
│                                    │                             │
│                                    ▼                             │
│                            Response + Sources                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Breakdown

### 2.1 Ingestion Pipeline

**Input sources:**
- ICAR Package-of-Practices PDFs (one per crop, per state — ~400 documents)
- KVK booklets from agritech.tnau.ac.in and ICAR portal
- PMFBY/PMKISAN/KCC scheme documents (govt. websites)

**Processing stages:**

```
Stage 1: Extraction
  PDF → PyMuPDF → raw text per page
  If text density < 50 chars/page → Tesseract OCR fallback

Stage 2: Chunking
  Strategy: Recursive character splitter
  Chunk size: 512 tokens (GPT-4 tokenizer approximation)
  Overlap: 64 tokens
  Split priority: paragraph → sentence → word

Stage 3: Metadata Tagging
  Each chunk gets:
    - source_file: str          (filename)
    - source_title: str         (document title)
    - state: str | "pan-india"  (from filename pattern or NER)
    - agro_zone: str            (from state → zone lookup table)
    - crop: str | None          (extracted from title or content)
    - topic: str                (pest | disease | irrigation | 
                                 fertilizer | harvest | scheme)
    - language: str             (detected by langdetect)
    - page_number: int

Stage 4: Embedding
  Model: paraphrase-multilingual-MiniLM-L12-v2 (384 dim)
  Batch size: 64
  Device: CPU (MPS/CUDA if available)
  Normalize: L2 normalize all vectors

Stage 5: Indexing
  FAISS index type: IndexFlatIP (inner product = cosine on normalized vecs)
  Upgrade path: IndexIVFFlat with nlist=100 if chunks > 50k
  Stored alongside: chunks.pkl (list of dicts with all metadata)
  Save: faiss.index + chunks.pkl to data/ directory
```

**Estimated corpus size:**
- ~400 PDFs × avg 30 pages × 2 chunks/page = ~24,000 chunks
- At 384 dim × float32 = ~36 MB for FAISS index (trivially fits in RAM)

---

### 2.2 Pincode Resolver

**Logic:**
```python
# pincode_mapper.py
# Uses a bundled pincode DB (CSV from data.gov.in, ~150k rows)
# Maps: pincode → district → state → agro_climatic_zone

ZONE_MAP = {
    "Punjab": "IGP-Northwest",
    "Haryana": "IGP-Northwest",
    "Uttar Pradesh": "IGP-Central",
    "Bihar": "IGP-East",
    "West Bengal": "Eastern",
    "Odisha": "Eastern",
    "Maharashtra": "Deccan",
    "Karnataka": "Deccan-South",
    "Andhra Pradesh": "Deccan-South",
    "Telangana": "Deccan-South",
    "Tamil Nadu": "South",
    "Kerala": "South-Coastal",
    "Gujarat": "Arid-Semi",
    "Rajasthan": "Arid",
    "Madhya Pradesh": "Central",
    "Chhattisgarh": "Central",
    "Assam": "Northeast",
    # ... all 28 states + 8 UTs
}
```

**Fallback chain:**
1. Exact pincode match in bundled DB
2. First 3 digits (postal division) → approximate state
3. If still unknown → retrieve without region filter

---

### 2.3 Region-Aware Retriever

**Algorithm:**

```python
def retrieve(query: str, state: str | None, top_k: int = 5):
    # Step 1: Embed query
    query_vec = embedder.encode([query], normalize=True)  # (1, 384)
    
    # Step 2: FAISS search over ALL chunks (fast, ~5ms for 24k chunks)
    scores, indices = faiss_index.search(query_vec, top_k * 4)
    
    # Step 3: Apply region-aware re-ranking
    candidates = []
    for score, idx in zip(scores[0], indices[0]):
        chunk = chunks[idx]
        
        # Boost: exact state match
        if state and chunk["state"] == state:
            score += BOOST_EXACT_STATE      # +0.20
        
        # Boost: same agro-climatic zone
        elif state and chunk["agro_zone"] == STATE_TO_ZONE[state]:
            score += BOOST_SAME_ZONE        # +0.10
        
        # Boost: pan-india documents always relevant
        elif chunk["state"] == "pan-india":
            score += BOOST_PAN_INDIA        # +0.05
        
        candidates.append((score, chunk))
    
    # Step 4: Re-rank and return top_k
    candidates.sort(reverse=True)
    return candidates[:top_k]
```

**Why FAISS-first then re-rank (not metadata pre-filter):**
- FAISS IndexFlatIP doesn't support metadata filtering natively
- Pre-filtering would require IndexIVFFlat + custom selector (complex)
- Post-retrieval re-ranking is simpler, fast enough, and allows pan-india docs to compete

---

### 2.4 LLM Generator (Gemini 1.5 Flash)

**System prompt structure:**

```
ROLE: You are KrishiGPT, an expert agricultural advisor for Indian farmers.
      You are trusted by farmers and always give practical, actionable advice.

REGIONAL CONTEXT: {farmer is from district X, state Y, agro-climatic zone Z}

LANGUAGE INSTRUCTION: Respond ONLY in {language_name}. 
Use simple words that a farmer with primary-school education can understand.
Avoid scientific jargon unless you immediately explain it in simple terms.

RETRIEVED CONTEXT:
[Source 1: ICAR Package of Practices for Paddy, Karnataka, Zone: Deccan-South]
{chunk_text}

[Source 2: PMFBY Scheme Guidelines 2024, Pan-India]
{chunk_text}

QUESTION: {farmer_question}

INSTRUCTIONS:
- Answer directly and concisely (3-5 sentences max for simple questions)
- For pest/disease questions: name the problem, give immediate treatment, give prevention
- For scheme questions: state eligibility, enrollment process, documents needed
- Always end with one practical tip specific to {state} conditions
- If the retrieved context doesn't contain the answer, say "I don't have reliable 
  information about this for your region. Please contact your local KVK at [number]."
- NEVER make up dosage numbers, dates, or eligibility criteria not in the context

OUTPUT FORMAT:
Respond in {language_name} only. No mixing of languages.
```

**Token budget:**
- System prompt: ~400 tokens
- Context chunks (5 × 512 tokens): ~2,560 tokens
- Question: ~50 tokens
- Total input: ~3,010 tokens (well within Gemini Flash 1M context)
- Max output: 500 tokens

**Gemini Flash is chosen because:**
- Free tier: 15 RPM, 1M tokens/day (sufficient for MVP)
- 1M context window (can fit all retrieved chunks easily)
- Multilingual capability covers all 7 target languages
- 2–4 second latency on typical queries

---

### 2.5 Translation Layer (Bhashini)

**When used:**
- Input is detected as non-English → translate TO English for retrieval
- Output is always generated in detected language (Gemini handles this)
- TTS: convert response text → audio for voice output

**Why not translate everything through Bhashini:**
- Gemini 1.5 Flash natively handles all 7 languages well
- Translation adds latency; only use for very low-resource languages
- For Hindi/Tamil/Telugu/Kannada: Gemini responds directly

**Bhashini endpoints used:**
```
POST /ulca/api/v0/model/compute  (translation)
POST /ulca/api/v0/model/compute  (TTS - different modelId)
POST /ulca/api/v0/model/compute  (ASR - for voice input)
```

---

### 2.6 WhatsApp Integration (Twilio)

**Webhook flow:**
```
Twilio → POST /webhook/whatsapp
  ├── Validate Twilio signature (X-Twilio-Signature header)
  ├── Parse: From, Body, MediaUrl (if voice/image)
  ├── Load session from Redis (keyed by phone number hash)
  │     └── session = {language, pincode, conversation_history[-5]}
  ├── If MediaUrl → download → Bhashini ASR → text
  ├── Call RAG pipeline
  ├── Save session to Redis (TTL: 24 hours)
  └── Respond via Twilio MessagingResponse

Rate limiting: 10 messages/hour per phone number (Redis counter)
```

**Session state:**
```json
{
  "phone_hash": "sha256(+91XXXXXXXXXX)",
  "language": "hi",
  "pincode": "560001",
  "state": "Karnataka",
  "agro_zone": "Deccan-South",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "message_count_today": 3,
  "created_at": "2026-06-16T10:00:00Z",
  "last_active": "2026-06-16T14:30:00Z"
}
```

---

### 2.7 Caching Strategy

**Redis caching:**
```
Key: "query:{sha256(query + state + language)}"
Value: full ChatResponse JSON
TTL: 1 hour

Key: "pincode:{pincode}"
Value: region info JSON
TTL: 30 days (pincodes don't change)

Key: "session:{phone_hash}"
Value: session JSON
TTL: 24 hours
```

**Why cache queries:**
- Farmers often ask the same questions (when to sow paddy, urea dose for wheat)
- Cache hit rate expected: 20–30% in production
- Reduces Gemini API calls significantly

---

## 3. Data Flow Diagrams

### 3.1 Text Query (Web)

```
User types question + selects language + enters pincode
        │
        ▼
Next.js POST /api/chat
        │
        ▼
FastAPI /chat endpoint
        │
        ├─► Redis cache check ── HIT ──► return cached response
        │
        └─► MISS
                │
                ▼
        Pincode → state + zone
                │
                ▼
        Embed query (multilingual MiniLM)
                │
                ▼
        FAISS search (top 20)
                │
                ▼
        Region re-ranking (top 5)
                │
                ▼
        Build prompt with context
                │
                ▼
        Gemini 1.5 Flash generate
                │
                ▼
        Store in Redis cache
                │
                ▼
        Return: {response, sources, region, latency}
                │
                ▼
Next.js renders response with source bubbles
```

### 3.2 Voice Query (WhatsApp)

```
Farmer sends voice note on WhatsApp
        │
        ▼
Twilio → POST /webhook/whatsapp
        │
        ├─► Validate Twilio signature
        ├─► Load Redis session (language, pincode)
        │
        ▼
Download audio (Twilio MediaUrl)
        │
        ▼
Bhashini ASR → transcribed text + detected language
        │
        ▼
[ same as text query from here ]
        │
        ▼
Bhashini TTS → audio (optional, if session.voice_enabled)
        │
        ▼
Twilio: send text response + audio URL (if TTS enabled)
```

---

## 4. Database Schema

### PostgreSQL

```sql
-- Session storage (long-term, for analytics)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_hash TEXT,              -- SHA256 of phone number
    channel TEXT,                 -- 'whatsapp' | 'web'
    language TEXT NOT NULL,
    pincode TEXT,
    state TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_active TIMESTAMPTZ DEFAULT now()
);

-- Message log (for eval and improvement)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    role TEXT NOT NULL,           -- 'user' | 'assistant'
    content TEXT NOT NULL,
    language TEXT,
    sources JSONB,                -- array of source doc references
    latency_ms INTEGER,
    feedback SMALLINT,            -- 1 = thumbs up, -1 = thumbs down, 0 = no feedback
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Corpus metadata (one row per document, not per chunk)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    title TEXT,
    source_url TEXT,
    state TEXT,
    agro_zone TEXT,
    crop TEXT,
    topic TEXT,
    chunk_count INTEGER,
    ingested_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 5. Deployment Architecture

### Development
```
localhost:3000  Next.js dev server
localhost:8000  FastAPI uvicorn
localhost:5432  PostgreSQL (Docker)
localhost:6379  Redis (Docker)
```

### Production (Railway / Render free tier)
```
Railway Service 1: FastAPI backend (512 MB RAM, 1 vCPU)
Railway Service 2: Next.js frontend (auto-scaled)
Railway Postgres:  500 MB free tier
Railway Redis:     25 MB free tier (sufficient for session cache)
```

**FAISS index hosting:**
- Index files (faiss.index + chunks.pkl, ~40MB) committed to repo or stored in Railway volume
- Loaded into memory at startup (~2 seconds)
- No external vector DB needed (simplicity > scalability for MVP)

---

## 6. Security Architecture

```
Public endpoints:
  GET  /health          - no auth
  GET  /languages       - no auth
  POST /chat            - rate limited by IP (10 req/min)
  POST /webhook/whatsapp - Twilio signature required

No endpoints expose:
  - Raw corpus text
  - Phone numbers
  - Session data
  - FAISS index directly

Environment variables:
  All secrets via .env / Railway environment vars
  Never in source code or logs

Logging rules:
  Log: query_hash, language, state, latency_ms, feedback
  Never log: full query text (PII risk), phone numbers, pincode
```

---

## 7. Scalability Path

| Stage | Load | Changes |
|---|---|---|
| MVP (now) | 50 concurrent | Single FastAPI, FAISS in memory, Gemini Flash |
| v1 (3 months) | 500 concurrent | Add worker pool, Redis queue for Gemini calls |
| v2 (6 months) | 5k concurrent | Qdrant/Weaviate instead of FAISS, LLM load balancer |
| v3 (production) | 50k concurrent | Kubernetes, dedicated embedding service, fine-tuned model |

---

## 8. Key Design Decisions and Rationale

| Decision | Alternative Considered | Why This Choice |
|---|---|---|
| FAISS + post-filter re-ranking | Qdrant with native metadata filter | Simpler; 24k chunks fits in RAM; zero infra cost |
| Gemini 1.5 Flash | Self-hosted Llama-3-8B | Free tier covers MVP; multilingual out-of-box; 4s vs 20s latency on CPU |
| Multilingual MiniLM | MuRIL (Google) | MuRIL is better for Indic but heavier (471MB vs 117MB); MiniLM sufficient for retrieval |
| Bhashini for ASR/TTS | Google Cloud Speech | Bhashini is free for Indian languages; better IndicASR accuracy |
| FastAPI | Django / Flask | Async support for concurrent LLM calls; automatic OpenAPI docs |
| Docker Compose | Kubernetes | Complexity vs benefit for MVP; Railway handles orchestration |
| Redis for sessions | PostgreSQL only | Sub-millisecond session reads; essential for WhatsApp latency budget |
