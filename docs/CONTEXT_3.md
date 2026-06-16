# CONTEXT_3.md — KrishiGPT (checkpoint 3): Provider Failover + Evaluation Results

> Read CONTEXT.md → CONTEXT_2.md → this file in order. This checkpoint covers the
> multi-provider failover (Gemini + Groq) and the **Phase 4 evaluation results** —
> the numbers for the presentation. Last updated: 2026-06-16 (after Phase 4).

---

## Headline result (Phase 4 ablation)

Region-aware retrieval vs a no-region baseline, on the 20-question manual eval set
(`backend/data/eval/manual_eval.jsonl`; 7 languages; region metrics over the 16
state-specific questions; faithfulness on the 10 English questions).

| Metric | No region (baseline) | KrishiGPT (region-aware) |
|---|---|---|
| **Top-1 from correct state** | 56% | **100%** |
| **Region hit@5** | 75% | **100%** |
| **MRR (state)** | 0.664 | **1.000** |
| **Hallucination rate** | 20% | **0%** |
| Faithfulness (token-overlap) | 64% | 66% |

**The one-line claim:** *Region-aware re-ranking moves the correct-state document to
rank #1 from 56% → 100% of the time, and drops hallucination 20% → 0% on our eval set.*

### What each metric means (so you can defend it to a jury)
- **Top-1 from correct state** — is the #1 retrieved document from the farmer's actual
  state? This is the most direct effect of the +0.20 state boost. Baseline gets the wrong
  state at rank 1 nearly half the time.
- **Region hit@5** — is a correct-state doc anywhere in the top 5?
- **MRR (state)** — reciprocal rank of the first correct-state doc (1.0 = always rank 1).
- **Hallucination rate** — fraction of English answers whose content words are <50%
  grounded in the retrieved chunk text (token-overlap proxy, not a heavy NLI model —
  intentional for the 14h build). When wrong-state docs are retrieved, the model grounds
  on irrelevant text and hallucinates; region-grounding removed it here.
- **Faithfulness** — mean token-overlap of answer vs retrieved context.

### Honesty caveat (state this if asked)
Numbers are on a **small demo corpus (45 chunks, 12 states) and 20 questions**. They are
clean partly because the corpus is well-separated. Frame as "on our evaluation set," not a
production-scale generalization claim. Methodology is sound; scale is mini-project scale.

### How to reproduce
```powershell
.\.venv\Scripts\python.exe scripts\evaluate.py                 # full (uses LLM for faithfulness)
.\.venv\Scripts\python.exe scripts\evaluate.py --no-generation # retrieval metrics only, ZERO quota
```
Results are also written to `backend/data/eval/results.json`.

---

## Multi-provider failover (new)

The generator (`backend/rag/generator.py`) now has a provider chain so the eval (40 calls)
and the live demo never stall on Gemini's free-tier limit (20 requests/day per model).

**Order:** Gemini key #1 → … → Gemini key #N → **Groq fallback**.

- **Gemini key rotation:** set `GOOGLE_API_KEY` (single) and/or `GOOGLE_API_KEYS`
  (comma-separated, no spaces). On a 429/quota error the generator rotates to the next key
  and sticks with whichever works.
- **Groq fallback:** set `GROQ_API_KEY` (model via `GROQ_MODEL`, default
  `llama-3.3-70b-versatile`). Used **only** when all Gemini keys are quota-exhausted.
  Verified working: produces grounded, attributed answers.
- **Why Gemini stays primary:** best multilingual quality for the 7 Indic languages
  (Kannada/Tamil/Telugu/etc.). Groq's Llama is the safety net, strong for English.
- **Graceful stub:** if NO provider key is set, `generate()` returns a retrieved-snippet
  stub so the rest of the system stays testable.

New deps/env: `groq` (in requirements.txt); `GROQ_API_KEY`, `GROQ_MODEL`,
`GOOGLE_API_KEYS` in `.env` / `.env.example`.

> NOTE: Gemini free-tier quota for today was already exhausted during testing, so the eval
> faithfulness calls actually ran on Groq via failover. The demo will use Gemini again once
> the daily quota resets (≈ midnight Pacific) — or immediately if you add more Gemini keys
> to `GOOGLE_API_KEYS`.

---

## Eval design notes (why the metrics changed)

The first eval attempt used **precision@8**, which was misleading: each state has only
2–4 chunks in the corpus, so precision@8 is structurally capped low (you can't fill 8 slots
with same-state chunks). Replaced with **Top-1 / RegionHit@5 / MRR**, which measure *ranking
quality* — exactly where the region boost helps — and are honest for a small corpus.

Retrieval metrics use **zero LLM calls** (deterministic). Generation/faithfulness is a
separate, quota-aware step that retries transient errors and **skips** (does not abort) on
failure, so a flaky call never wipes the whole run.

---

## State of the build after Phase 4

| Phase | Status |
|---|---|
| 0 Scaffold | ✅ |
| 1 Ingestion | ✅ |
| 2 RAG pipeline | ✅ live-tested |
| Corpus expansion | ✅ 45 chunks / 12 states |
| 3 Frontend | ✅ end-to-end verified |
| Provider failover | ✅ Gemini rotation + Groq fallback, tested |
| 4 Evaluation | ✅ **done — table above** |
| 5 Polish | ⏭️ next (all-7-language test, I-don't-know cases, branding) |
| 6 WhatsApp/voice | code written, untested (needs Twilio + ngrok + Bhashini) |
| 7 Buffer | pending (final testing, demo rehearsal, commit) |

### Run commands (unchanged — see CONTEXT_2.md §"How to run")
- Backend: from `backend/`, `..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000`
- Frontend: from `frontend/`, `npm run dev` → http://localhost:3000
- Restart the backend after pulling these changes (warmup + new env are read at startup).
