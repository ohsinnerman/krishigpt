# CONTEXT.md — KrishiGPT Build State & Working Context

> Living document. Read this first when resuming work. It records **what KrishiGPT is**,
> **what has been built so far**, **what deviates from the original spec and why**, and
> **exactly how to run, rebuild, and continue**. Last updated: 2026-06-16.

---

## 0. The One-Line Goal

Build a **region-aware multilingual RAG agricultural advisor** for Indian farmers, working
end-to-end for a **college mini-project presentation in ~14 hours**. The research claim (the
single number that matters for the presentation) is:

> **Region-aware retrieval reduces hallucination vs a no-region baseline** — demonstrated via
> an ablation in `scripts/evaluate.py`.

The demo story: *change the farmer's PIN code and the retrieved source documents change* —
a Karnataka pincode surfaces Karnataka paddy docs; a Punjab pincode surfaces Punjab wheat docs.

---

## 1. What This Project Is

KrishiGPT answers farming questions in up to 7 Indic languages by:
1. Resolving the farmer's PIN code → state → agro-climatic zone.
2. Embedding the question (multilingual MiniLM, 384-dim).
3. FAISS search over a corpus of agricultural docs (over-fetch top_k×4 candidates).
4. **Region-aware re-ranking**: boost chunks matching the farmer's state (+0.20),
   same agro-zone (+0.10), or pan-india (+0.05).
5. Synthesizing an answer with Google Gemini, constrained to the retrieved context and
   forced into the target language/script.

Full original specification lives in **`docs/`** (MASTER_PROMPT.md is the authoritative one;
PRD/ARCHITECTURE/DATA/EVALUATION/PIPELINE/DEPLOYMENT/API support it).

---

## 2. Environment (the real machine, not the spec's assumptions)

| Tool | Spec assumed | Actually present | Consequence |
|---|---|---|---|
| Python | 3.11 | **3.13.12** only | Relaxed version pins; switched off fragile pinned wheels |
| Node | 20+ | **22.15.0** | fine |
| Next.js | 14 | **16.2.9** (scaffolded fresh) | See §6 — v16 has breaking changes, reviewed |
| Docker | required | installed & running | Not used for app; available for Redis if wanted |
| Redis | on 6379 | was occupied, now free | App treats Redis as **optional** (graceful degrade) |
| ngrok | needed for WhatsApp | **3.37.3** installed | for Phase 6 |
| OS | — | Windows 11, PowerShell + Git Bash | path/shell quirks handled |

**Decisions locked with the user:**
- Run mode: **local Python + local Node** for the app (no full Docker Compose). Redis optional.
- Gemini API key: user **has** one (to be pasted into `backend/.env`).
- Scope (must-haves): **web chat + region demo + eval number + all 7 languages + WhatsApp/voice**.
  Live deployment **dropped** (localhost + ngrok is enough for the demo).

---

## 3. Key Deviations From `docs/MASTER_PROMPT.md` (and why)

1. **Gemini SDK swapped.** Spec used `google-generativeai` (`genai.GenerativeModel`). That
   package's support has officially ended and emits a FutureWarning. **Switched to the current
   `google-genai` SDK** (`from google import genai`, `genai.Client(...).models.generate_content`).
   Default model moved from retired `gemini-1.5-flash` → **`gemini-2.0-flash`** (override via
   `GEMINI_MODEL` env var).
2. **Requirements unpinned/relaxed** for Python 3.13 + Windows compatibility (faiss-cpu,
   sentence-transformers, etc.). Behavior preserved, exact versions not.
3. **Redis is optional.** All cache calls are wrapped; if Redis is absent the system still
   answers (just no cache). The spec assumed Redis always up.
4. **Corpus is a curated seed set, not scraped ICAR PDFs.** The spec's TNAU/ICAR download URLs
   are dead (404) and pincode CSV sources moved. `scripts/download_corpus.py` tries them
   best-effort, then **always writes 8 curated, state-tagged seed docs** so the region demo works
   regardless of network. This yields **17 chunks** — small, but enough to demonstrate region
   differentiation (the thing being evaluated). Expand the seed set or fix URLs for more volume.
5. **Pincode DB falls back to prefix mapping.** No `pincodes.csv` downloaded; the first-2-digit
   → state map in `pincode_mapper.py` resolves every pincode (district shows as "Unknown").
6. **No Postgres.** Sessions/messages persistence is out of scope for the 14h build; WhatsApp
   sessions are in-memory. (`models/` exists but is unused.)
7. **Eval faithfulness uses a token-overlap proxy**, not a heavy NLI model, to avoid a large
   extra download. Good enough to show the region vs no-region delta for the presentation.
8. **Docs moved to `/docs`.** README.md stays at repo root.

---

## 4. Current Build State (phase by phase)

Ordering is **demo-first** (eval before WhatsApp), differs slightly from PIPELINE.md.

- **Phase 0 — Scaffold: ✅ DONE.** Directory structure, `requirements.txt`, `.env.example`,
  `.gitignore`, venv created, all backend deps installed (exit 0), `main.py` boots logic written.
- **Phase 1 — Ingestion: ✅ DONE.** Chunker/ingest/embeddings/vector_store/pincode_mapper written.
  Seed corpus generated. **FAISS index built: 17 chunks, 6 regions**, stored at
  `backend/data/faiss.index` + `backend/data/chunks.pkl`. Region re-ranking verified working
  (Karnataka paddy chunk: 0.459 → **0.659** with region boost).
- **Phase 2 — RAG pipeline: 🟡 IN PROGRESS.** retriever + generator + pipeline + `/chat` wiring
  all written. Generator migrated to new SDK. **NOT yet tested with a live Gemini key** — needs
  `GOOGLE_API_KEY` in `backend/.env`. Without the key it runs in "demo mode" (returns retrieved
  snippet) so the rest of the stack is testable.
- **Phase 3 — Frontend: ✅ written, ⏳ not yet run.** Next.js 16 app scaffolded; single polished
  client page (`frontend/src/app/page.tsx`) with language selector (7 langs), pincode input +
  region badge, example questions (all 7 langs), collapsible sources, mobile layout.
- **Phase 4 — Evaluation: ✅ written, ⏳ not yet run.** `scripts/evaluate.py` runs the ablation
  (region vs no-region) over `backend/data/eval/manual_eval.jsonl` (20 questions, 7 languages).
- **Phase 5 — Polish: pending.**
- **Phase 6 — WhatsApp + voice: ✅ code written, ⏳ not wired.** `integrations/whatsapp.py` +
  `integrations/bhashini.py` done; needs ngrok + Twilio sandbox + Bhashini keys.
- **Phase 7 — Buffer/testing/demo rehearsal: pending.**

---

## 5. Repository Layout (current)

```
krishigpt/
├── CONTEXT.md                 ← this file
├── README.md
├── .env.example               ← template (GEMINI_MODEL=gemini-2.0-flash)
├── .gitignore                 ← ignores .env, .venv, node_modules, index artifacts, corpus
├── docs/                      ← all original spec docs (MASTER_PROMPT.md is authoritative)
├── .venv/                     ← Python 3.13 venv (gitignored)
├── backend/
│   ├── main.py                ← FastAPI app: /chat /health /languages /pincode/{} /webhook/whatsapp /feedback
│   ├── requirements.txt
│   ├── .env                   ← REAL secrets, gitignored. NEEDS GOOGLE_API_KEY.
│   ├── rag/
│   │   ├── embeddings.py       ← MiniLM loader, embed_texts/embed_query (normalized)
│   │   ├── vector_store.py     ← FAISS IndexFlatIP build/save/load/search
│   │   ├── retriever.py        ← region-aware re-ranking (THE core innovation)
│   │   ├── generator.py        ← Gemini via google-genai SDK + script validation + demo-mode stub
│   │   └── pipeline.py         ← orchestration, optional Redis cache, region_filter toggle
│   ├── data/
│   │   ├── ingest.py           ← PDF/HTML/TXT → chunks → embeddings → FAISS
│   │   ├── pincode_mapper.py   ← pincode → state/zone (CSV + prefix fallback)
│   │   ├── corpus/             ← 8 seed .txt docs (gitignored)
│   │   ├── eval/manual_eval.jsonl  ← 20 eval questions
│   │   ├── faiss.index         ← built index (gitignored)
│   │   └── chunks.pkl          ← chunk metadata (gitignored)
│   ├── integrations/
│   │   ├── whatsapp.py         ← Twilio webhook handler, onboarding flow, in-memory sessions
│   │   └── bhashini.py         ← ASR / translate / TTS (no-op without Bhashini keys)
│   ├── models/                 ← (unused placeholder)
│   └── tests/test_pincode.py   ← pincode mapper unit tests (pass)
├── frontend/                  ← Next.js 16 app
│   ├── .env.local             ← NEXT_PUBLIC_API_URL=http://localhost:8000
│   └── src/
│       ├── app/page.tsx        ← the whole chat UI (client component)
│       └── lib/{api.ts,types.ts,constants.ts}
└── scripts/
    ├── download_corpus.py      ← best-effort downloads + guaranteed seed corpus + pincode CSV
    ├── build_index.py          ← pins output paths to backend/data/, runs ingestion
    └── evaluate.py             ← region vs no-region ablation → results.json + printed table
```

---

## 6. Next.js 16 Notes (reviewed against installed docs)

`frontend/AGENTS.md` warns this Next.js differs from training data. Reviewed
`node_modules/next/dist/docs/01-app/02-guides/upgrading/version-16.md`. **None of the v16
breaking changes affect our code** — the page is a pure client component (`"use client"`,
hooks, `fetch`, `NEXT_PUBLIC_*`). Not using async params/searchParams, middleware→proxy,
next/image, PPR, or runtime config. Turbopack-by-default is fine. `next lint` removed (we don't
rely on it).

**IDE diagnostics caveat:** the editor's Python interpreter is the **system Python313**, not our
`.venv`, so it reports "package not installed" / "cannot find google.genai". These are false for
our runtime — we always invoke `.venv/Scripts/python.exe`. To silence, point the IDE interpreter
at `.venv/Scripts/python.exe`.

---

## 7. How To Run (Windows)

**0) Add the Gemini key** (required for real answers):
```
# edit backend/.env  →  GOOGLE_API_KEY=AIza...your_key...
```

**1) Rebuild the index** (only if corpus changed):
```bash
./.venv/Scripts/python.exe scripts/build_index.py
```

**2) Start the backend** (from backend/ so relative data paths resolve):
```bash
cd backend
../.venv/Scripts/python.exe -m uvicorn main:app --reload --port 8000
# health check:  curl http://localhost:8000/health
```

**3) Start the frontend:**
```bash
cd frontend
npm run dev          # http://localhost:3000
```

**4) Run the eval (the presentation number):**
```bash
./.venv/Scripts/python.exe scripts/evaluate.py
```

**5) WhatsApp (Phase 6, optional):**
```bash
ngrok http 8000
# set Twilio sandbox webhook → https://<ngrok>/webhook/whatsapp
# put TWILIO_* and BHASHINI_* in backend/.env
```

---

## 8. Verified-Working Facts (don't re-litigate)

- Backend dependencies install cleanly on Python 3.13 (pip exit 0).
- Embedding model `paraphrase-multilingual-MiniLM-L12-v2` downloads & caches; embeds fine.
- FAISS index loads (17 vectors) when backend runs **from `backend/`**.
- Pincode prefix fallback: 560001→Karnataka, 110001→Delhi, 141001→Punjab. Tests pass.
- Region boost is real and visible: same query/pincode gives a higher score & better state
  ordering with `region_filter=True` than `False`.

## 9. Known Risks / TODO when resuming

- [ ] **Phase 2 test pending:** paste `GOOGLE_API_KEY`, then verify `/chat` returns a real
      answer in English AND Hindi (Devanagari), sources non-empty, latency < 10s.
- [ ] Confirm `gemini-2.0-flash` is enabled on the user's key; if not, set `GEMINI_MODEL`
      to whatever Flash model the key has (e.g. `gemini-2.5-flash`).
- [ ] 17 chunks is thin — if eval numbers look noisy, expand `SEED_DOCS` in
      `scripts/download_corpus.py` and rebuild.
- [ ] Frontend never run yet — run `npm run dev` and confirm it talks to the backend (CORS is `*`).
- [ ] WhatsApp/Bhashini untested end-to-end (needs external accounts).
```
