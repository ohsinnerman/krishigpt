# KrishiGPT 🌾

> Region-aware multilingual RAG agricultural advisor for Indian farmers

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)

---

## What is KrishiGPT?

KrishiGPT is an open-source agricultural advisory chatbot that answers farmer questions in **seven Indic languages** by retrieving from a curated corpus of ICAR Package-of-Practices PDFs, KVK booklets, and government scheme documents (PMFBY, PMKISAN, KCC).

The core defensible innovation is **region-prioritized retrieval**: every document chunk is tagged with state and agro-climatic zone, and the retriever filters by the farmer's pin code before LLM synthesis. This approach mirrors the AgriRegion paper (arXiv:2512.10114) which reports 10–20% hallucination reduction from geographic grounding.

---

## Why This Matters

- ~70% of Indian farmers are vernacular and low-literacy (NITI Aayog 2024)
- Existing chatbots like Wadhwani AI's Kisan-eMitra prove demand but are closed-source
- No open-source system combines region-awareness + voice-first UX in seven languages
- ICAR Package-of-Practices documents are public but not machine-accessible

---

## Key Features

| Feature | Description |
|---|---|
| **Region-aware retrieval** | Pin code → state → agro-climatic zone → filtered FAISS search |
| **7 Indic languages** | English, Hindi, Kannada, Tamil, Telugu, Marathi, Gujarati, Punjabi |
| **Voice-first UX** | Bhashini ASR/TTS for low-literacy farmers |
| **Multi-modal (v2)** | Leaf photo → diagnosis → treatment retrieval |
| **WhatsApp + Web** | Twilio Business API + Next.js web interface |
| **Scheme awareness** | PMFBY, PMKISAN, KCC eligibility and application guidance |

---

## Tech Stack

```
Frontend      Next.js 14 + Tailwind CSS + shadcn/ui
Backend       FastAPI (Python 3.11)
RAG           LangChain + FAISS + sentence-transformers
Embeddings    paraphrase-multilingual-MiniLM-L12-v2 (MuRIL for v2)
Generator     Gemini 1.5 Flash (primary) / Llama-3-8B (self-hosted fallback)
Translation   IndicTrans2 via Bhashini API
ASR/TTS       Bhashini (free tier)
WhatsApp      Twilio WhatsApp Business API
Database      PostgreSQL (sessions) + Redis (cache)
Infra         Docker Compose → Railway/Render (free tier)
```

---

## Repository Structure

```
krishigpt/
├── backend/
│   ├── main.py                    # FastAPI entrypoint
│   ├── rag/
│   │   ├── pipeline.py            # Core RAG orchestration
│   │   ├── embeddings.py          # Embedding model wrapper
│   │   ├── vector_store.py        # FAISS index management
│   │   ├── retriever.py           # Region-aware retrieval logic
│   │   └── generator.py           # LLM prompt + generation
│   ├── data/
│   │   ├── ingest.py              # PDF → chunks → FAISS
│   │   ├── pincode_mapper.py      # Pincode → state/zone lookup
│   │   ├── chunker.py             # Semantic chunking strategy
│   │   └── corpus/                # Raw PDFs (gitignored, see DATA.md)
│   ├── integrations/
│   │   ├── whatsapp.py            # Twilio webhook handler
│   │   ├── bhashini.py            # ASR/TTS/translation client
│   │   └── gemini.py              # Gemini API client
│   ├── models/
│   │   ├── session.py             # SQLAlchemy session model
│   │   └── feedback.py            # Farmer feedback model
│   └── tests/
│       ├── test_retrieval.py
│       ├── test_generation.py
│       └── test_whatsapp.py
├── frontend/
│   ├── app/
│   │   ├── page.tsx               # Landing page
│   │   ├── chat/page.tsx          # Web chat interface
│   │   └── api/chat/route.ts      # Next.js API proxy
│   ├── components/
│   │   ├── ChatWindow.tsx
│   │   ├── LanguageSelector.tsx
│   │   ├── PincodeInput.tsx
│   │   ├── SourceBubble.tsx       # Shows retrieved doc sources
│   │   └── VoiceButton.tsx        # Bhashini ASR trigger
│   └── lib/
│       └── api.ts                 # Backend API client
├── scripts/
│   ├── download_corpus.sh         # Downloads ICAR PDFs
│   ├── build_index.py             # Runs full ingestion pipeline
│   └── evaluate.py                # Runs eval on KCC transcripts
├── docker-compose.yml
├── .env.example
├── README.md
├── PRD.md
├── ARCHITECTURE.md
├── DATA.md
├── API.md
├── MULTILINGUAL.md
├── EVALUATION.md
├── DEPLOYMENT.md
└── MASTER_PROMPT.md
```

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/yourname/krishigpt
cd krishigpt

# 2. Copy env and fill in keys
cp .env.example .env

# 3. Download corpus and build index (takes ~20 min first time)
bash scripts/download_corpus.sh
python scripts/build_index.py

# 4. Start everything
docker-compose up

# 5. Open http://localhost:3000
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Gemini 1.5 Flash API key (free tier: 15 RPM) |
| `BHASHINI_USER_ID` | Yes | Bhashini platform user ID |
| `BHASHINI_API_KEY` | Yes | Bhashini ULCA API key |
| `TWILIO_ACCOUNT_SID` | Optional | WhatsApp integration |
| `TWILIO_AUTH_TOKEN` | Optional | WhatsApp integration |
| `TWILIO_WHATSAPP_NUMBER` | Optional | e.g. `whatsapp:+14155238886` |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |

---

## Research Context

This project implements the region-prioritized retrieval approach described in:

> AgriRegion: Geographic Grounding for Agricultural LLM Hallucination Reduction  
> arXiv:2512.10114, December 2025

A clean open-source clone with evaluation on Kisan Call Centre transcripts is publishable as an undergraduate workshop paper (ACL SRW, EMNLP findings, or ICON).

---

## License

MIT — see [LICENSE](LICENSE)
