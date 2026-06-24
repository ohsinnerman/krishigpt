# Corpus Sources & Provenance

KrishiGPT's knowledge base is a **curated prototype corpus** modeled on:

- **ICAR Package of Practices** (state agricultural universities / KVK crop production guides)
- **Government of India scheme guidelines** — PMFBY (pmfby.gov.in), PM-KISAN (pmkisan.gov.in),
  Kisan Credit Card (RBI/NABARD)

## Why a curated corpus (not live PDFs)

The original build spec pointed at public ICAR/TNAU PDF/HTML URLs and a data.gov.in pincode
CSV. At build time those public endpoints returned HTTP 404 (links had moved/expired). To keep
the prototype fully functional and reproducible offline, the corpus is authored as detailed,
state-tagged documents that mirror the structure and agronomic content of real ICAR Package of
Practices (varieties, sowing, fertilizer schedule, irrigation, pests & diseases with dosages,
weed management, harvest/yield). The pincode→state mapping uses a first-two-digit postal-prefix
fallback (see `backend/data/pincode_mapper.py`).

The agronomic facts (e.g. Cartap hydrochloride 4G at 25 kg/ha for paddy stem borer; wheat NPK
120:60:30; PMFBY farmer premium 2% Kharif / 1.5% Rabi) reflect widely published ICAR/extension
recommendations and scheme rules. They are **illustrative for a prototype** and should be
verified against the latest official notification before any real-world advisory use.

## Corpus at a glance

- 26 documents → ~101 indexed chunks across 13+ states and pan-India schemes.
- Crops: paddy, ragi, wheat, sugarcane, cotton, groundnut, soybean, mustard, chickpea,
  bajra, chilli, turmeric, coconut, rubber, tomato, onion.
- Schemes: PMFBY, PM-KISAN, KCC.

## How to refresh / extend

- Edit `scripts/seed_docs.py` (the `SEED_DOCS` dict; filename embeds the state).
- Run `python scripts/download_corpus.py` then `python scripts/build_index.py`.
- To ingest **real** PDFs instead, drop them into `backend/data/corpus/` with a
  `<crop>_<state>_*.pdf` filename and rebuild — `data/ingest.py` extracts and tags them.

## Honest framing for evaluation/demo

Present results as **"on our evaluation set"** with this prototype corpus — the contribution is
the region-aware retrieval method and its measured effect (correct-state document promoted to
rank #1, reduced hallucination), not a claim of production-scale ICAR ingestion.
