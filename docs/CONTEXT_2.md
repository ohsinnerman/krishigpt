# CONTEXT_2.md — KrishiGPT Run Guide & State (checkpoint 2)

> Continuation of `/CONTEXT.md`. Read CONTEXT.md first for the full picture; this file
> records progress since then and the exact commands to run everything yourself.
> Last updated: 2026-06-16 (after Phase 3).

---

## Progress since CONTEXT.md

| Phase | Status | Notes |
|---|---|---|
| 0 Scaffold | ✅ done | |
| 1 Ingestion | ✅ done | |
| 2 RAG pipeline | ✅ done + **live-tested** | Gemini works in EN, HI (Devanagari), KN (Kannada). Answers grounded & full. |
| Corpus expansion | ✅ done | **45 chunks across 12 states** (was 17/6). Added South (TN, Telangana, Kerala, AP chilli/turmeric) + North (UP, Haryana, Rajasthan). |
| 3 Frontend | ✅ done + **verified end-to-end** | Both servers ran, page rendered, CORS + /pincode + /chat all confirmed from browser origin. |
| 4 Evaluation | ⏭️ NEXT | Ablation region vs no-region. (One faithfulness-proxy fix pending — see §5.) |
| 5 Polish | pending | |
| 6 WhatsApp/voice | code written, untested | |
| 7 Buffer | pending | |

### Key changes made
- **Model:** switched to `gemini-2.5-flash` (env `GEMINI_MODEL`). Works correctly.
- **Thinking tokens fix:** `gemini-2.5-flash` spends output budget on hidden "thinking", which
  truncated answers to ~88 chars. Fixed in `backend/rag/generator.py` by setting
  `ThinkingConfig(thinking_budget=0)`. Answers are now full (~400–500 chars).
- **Corpus:** 22 seed docs total now (in `scripts/download_corpus.py` → `SEED_DOCS`). Rebuild any
  time with `scripts/build_index.py`.

### Verified region differentiation (the demo's core claim)
Same query "Which paddy variety and pest control should I use?", different pincode → different
top source state, each boosted to #1:
```
560001 Karnataka      -> Karnataka     score 0.679
600001 Tamil Nadu     -> Tamil Nadu    score 0.596
208001 Uttar Pradesh  -> Uttar Pradesh score 0.561
```
And same query with `region_filter=False` ranks a generic/other-state doc higher — that gap is
the research result.

---

## How to run everything yourself (Windows, two terminals)

> Run the **backend from the `backend/` folder** so its relative `data/` paths resolve.
> The frontend reads the backend URL from `frontend/.env.local` (already set to :8000).

### Terminal 1 — Backend (FastAPI on :8000)
```powershell
cd C:\Users\akuls\OneDrive\Documents\Projects\krishigpt\backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```
Wait for `Application startup complete.` then check health in a browser or another shell:
```powershell
curl http://localhost:8000/health
# -> {"status":"ok","chunks_loaded":45,"generator":"gemini-2.5-flash","gemini_configured":true,...}
```

### Terminal 2 — Frontend (Next.js on :3000)
```powershell
cd C:\Users\akuls\OneDrive\Documents\Projects\krishigpt\frontend
npm run dev
```
Open **http://localhost:3000**.

### Demo flow in the browser
1. Enter PIN code `560001` → badge shows "Karnataka · Deccan-South".
2. Click an example question, or type "How do I control stem borer in paddy?" → answer + sources.
3. Change language dropdown to हिन्दी, PIN to `141001` (Punjab), ask about wheat → Hindi answer
   from Punjab docs.
4. Expand "Sources" to show the region-tagged documents. Switch PIN to show sources change.

### Rebuild the FAISS index (only after editing the corpus)
```powershell
cd C:\Users\akuls\OneDrive\Documents\Projects\krishigpt
.\.venv\Scripts\python.exe scripts\build_index.py
```

### Stop servers
Press `Ctrl+C` in each terminal. If a port is stuck:
```powershell
Get-NetTCPConnection -LocalPort 8000,3000 -State Listen | Select -Expand OwningProcess -Unique | % { Stop-Process -Id $_ -Force }
```

---

## Quick API tests (optional, no browser)
```powershell
# English, Telangana cotton
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" `
  -d '{\"message\":\"How do I control pink bollworm in cotton?\",\"language\":\"en\",\"pincode\":\"500001\"}'

# Pincode resolve (feeds the region badge)
curl http://localhost:8000/pincode/600001
```

---

## §5 — Pending fix before Phase 4 eval (so the number is honest)
`scripts/evaluate.py`'s faithfulness proxy currently compares the answer against source **titles**
only, which is too thin to measure grounding. Before reporting hallucination numbers, change it to
compare the answer against the actual retrieved **chunk text**. (The region/precision metrics are
already correct.) This is the first task when resuming Phase 4.

---

## Gotchas / notes
- **IDE shows "cannot find google.genai" / "package not installed":** false alarm. The editor's
  Python interpreter is the system Python313, not our `.venv`. Runtime always uses
  `.venv\Scripts\python.exe`. To fix the squiggles, point the IDE interpreter at
  `.venv\Scripts\python.exe`.
- **Don't print Indic text to the raw Windows console** in ad-hoc scripts (cp1252 crash). The API
  returns proper UTF-8 JSON, so the app is unaffected — this only bit a debug print.
- **Redis is optional.** No cache currently running; the app degrades gracefully.
- **Pincode district = "Unknown":** expected — no `pincodes.csv`, using first-2-digit→state
  fallback. State and agro-zone are correct, which is all the retriever needs.
- `.env` (with the real `GOOGLE_API_KEY`) is gitignored and must never be committed.
