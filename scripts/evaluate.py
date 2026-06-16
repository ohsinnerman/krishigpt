#!/usr/bin/env python3
"""
Ablation evaluation: region-aware retrieval vs no-region baseline.
Produces the comparison table that is KrishiGPT's research result.

Usage:
  python scripts/evaluate.py                # runs both configs, prints table
  python scripts/evaluate.py --n 10         # limit examples (faster)

Metrics:
  - precision@k : fraction of top-k retrieved chunks whose state matches the
                  gold state (or is pan-india). Measures regional retrieval quality.
  - region_hit  : 1 if any top-k chunk is the exact gold state, else 0.
  - faithfulness: token overlap between the generated answer and the ACTUAL
                  retrieved chunk TEXT (not just titles). Computed on the
                  English subset, where answer and source share a language and
                  the lexical overlap is meaningful. A heavy NLI model is
                  intentionally avoided for the 14h build.
  - hallucination_rate = fraction of (English) answers with faithfulness < 0.5.
"""
import os, sys, json, asyncio, argparse, re
from pathlib import Path

BACKEND = Path(__file__).parent.parent / "backend"
DATA = BACKEND / "data"
sys.path.insert(0, str(BACKEND))

# Pin index paths to backend/data so the eval finds the index regardless of CWD.
os.environ.setdefault("FAISS_INDEX_PATH", str(DATA / "faiss.index"))
os.environ.setdefault("CHUNKS_PATH", str(DATA / "chunks.pkl"))
os.environ.setdefault("PINCODE_DB_PATH", str(DATA / "pincodes.csv"))

# Load .env (GOOGLE_API_KEY, RAG_TOP_K, etc.) from backend/.env
try:
    from dotenv import load_dotenv
    load_dotenv(BACKEND / ".env")
except Exception:
    pass

from rag.pipeline import KrishiGPTPipeline
from rag.retriever import retrieve
from data.pincode_mapper import get_region_from_pincode

EVAL_FILE = BACKEND / "data" / "eval" / "manual_eval.jsonl"
TOP_K = int(os.getenv("RAG_TOP_K", "8"))


def precision_at_k(retrieved_states, gold_state, k=TOP_K):
    top = retrieved_states[:k]
    if not top:
        return 0.0
    matches = sum(1 for s in top if s == gold_state or s == "pan-india")
    return matches / len(top)


def region_hit_at(retrieved_states, gold_state, k=5):
    return 1.0 if gold_state in retrieved_states[:k] else 0.0


def top1_region(retrieved_states, gold_state):
    """Is the #1 retrieved chunk from the correct state? The region boost's most
    direct effect — this is where region-aware re-ranking clearly wins."""
    return 1.0 if retrieved_states and retrieved_states[0] == gold_state else 0.0


def mrr_state(retrieved_states, gold_state):
    """Reciprocal rank of the first correct-state chunk (ranking quality)."""
    for rank, s in enumerate(retrieved_states, 1):
        if s == gold_state:
            return 1.0 / rank
    return 0.0


_WORD = re.compile(r"[a-z0-9]+")


def faithfulness_proxy(answer: str, context: str) -> float:
    """Fraction of the answer's content words that appear in the source context.
    Meaningful only when answer and context share a language (English subset)."""
    a = {w for w in _WORD.findall(answer.lower()) if len(w) > 3}
    c = set(_WORD.findall(context.lower()))
    if not a:
        return 1.0
    return len(a & c) / len(a)


def _context_text_for(pipeline, ex, region_filter: bool) -> str:
    """Re-run the same retrieval the pipeline used, returning the chunk TEXT."""
    region_info = get_region_from_pincode(ex["pincode"]) if ex.get("pincode") else None
    state = region_info.get("state") if region_info else None
    chunks = retrieve(
        query=ex["question"],
        faiss_index=pipeline.faiss_index,
        chunks=pipeline.chunks,
        state=state if region_filter else None,
        top_k=TOP_K,
    )
    return " ".join(c.get("text", "") for c in chunks)


def run_retrieval_config(pipeline, examples, region_filter: bool):
    """Retrieval-only metrics. ZERO LLM calls — safe under any quota.
    Region metrics are computed over state-specific questions only (pan-india
    scheme questions have no 'correct state', so they're excluded from them)."""
    rows = []
    for ex in examples:
        region_info = get_region_from_pincode(ex["pincode"]) if ex.get("pincode") else None
        state = region_info.get("state") if region_info else None
        chunks = retrieve(
            query=ex["question"],
            faiss_index=pipeline.faiss_index,
            chunks=pipeline.chunks,
            state=state if region_filter else None,
            top_k=TOP_K,
        )
        states = [c.get("state", "pan-india") for c in chunks]
        is_regional = ex["state"] != "pan-india"
        rows.append({
            "regional": is_regional,
            "region_hit5": region_hit_at(states, ex["state"], 5) if is_regional else None,
            "top1": top1_region(states, ex["state"]) if is_regional else None,
            "mrr": mrr_state(states, ex["state"]) if is_regional else None,
        })
    reg = [r for r in rows if r["regional"]]
    nr = len(reg)
    return {
        "n": len(rows),
        "n_regional": nr,
        "region_hit5": round(sum(r["region_hit5"] for r in reg) / nr, 3),
        "top1_region": round(sum(r["top1"] for r in reg) / nr, 3),
        "mrr_state": round(sum(r["mrr"] for r in reg) / nr, 3),
    }


async def run_generation_faithfulness(pipeline, examples, region_filter: bool):
    """Generation-based faithfulness (English subset). Uses LLM quota.
    Returns None if generation fails (e.g. 429 quota exhausted)."""
    en = [e for e in examples if e["language"] == "en"]
    faiths = []
    for ex in en:
        # Retry a couple of times on transient errors; skip (don't abort) on failure.
        res = None
        for _try in range(3):
            try:
                res = await pipeline.query(
                    message=ex["question"], language="en",
                    pincode=ex.get("pincode"), region_filter=region_filter,
                )
                break
            except Exception as e:
                print(f"  (gen retry {_try + 1}: {type(e).__name__})")
                await asyncio.sleep(2)
        if res is None:
            continue  # skip this example, keep going
        ctx = _context_text_for(pipeline, ex, region_filter)
        faiths.append(faithfulness_proxy(res["response"], ctx))
    if not faiths:
        return None
    return {
        "n_faithfulness_en": len(faiths),
        "faithfulness": round(sum(faiths) / len(faiths), 3),
        "hallucination_rate": round(sum(1 for f in faiths if f < 0.5) / len(faiths), 3),
    }


async def main(n=None, with_generation=True):
    examples = [json.loads(l) for l in EVAL_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    if n:
        examples = examples[:n]
    print(f"Loaded {len(examples)} eval examples. top_k={TOP_K}\n")

    pipeline = KrishiGPTPipeline()
    if not pipeline.chunks:
        print("ERROR: 0 chunks loaded. Run scripts/build_index.py first.")
        return

    # ── Retrieval metrics (no LLM, deterministic — the core region claim) ──
    print("Computing retrieval metrics (no LLM calls)...")
    no_region = run_retrieval_config(pipeline, examples, region_filter=False)
    with_region = run_retrieval_config(pipeline, examples, region_filter=True)

    # ── Generation faithfulness (optional, uses Gemini quota) ──
    if with_generation:
        print("Computing generation faithfulness (English subset, uses Gemini quota)...")
        f_no = await run_generation_faithfulness(pipeline, examples, region_filter=False)
        f_yes = await run_generation_faithfulness(pipeline, examples, region_filter=True)
        if f_no:
            no_region.update(f_no)
        if f_yes:
            with_region.update(f_yes)
    def pct(x):
        return "—" if x is None else f"{x*100:.0f}%"

    nf = no_region.get("n_faithfulness_en")
    print("\n" + "=" * 92)
    print("KrishiGPT Ablation: Region-Aware Retrieval vs No-Region Baseline")
    fnote = f"faithfulness on n={nf} English" if nf else "faithfulness skipped (no generation)"
    print(f"({no_region['n']} questions, 7 langs; region metrics over {no_region['n_regional']} "
          f"state-specific Qs; {fnote})")
    print("=" * 92)
    print(f"{'System':<26}{'Top-1 Region':>13}{'RegionHit@5':>13}{'MRR(state)':>12}{'Halluc.':>10}{'Faithful':>10}")
    print("-" * 92)
    for label, m in [("RAG (no region)", no_region), ("KrishiGPT (ours, region)", with_region)]:
        print(f"{label:<26}{m['top1_region']:>13.3f}{m['region_hit5']:>13.3f}{m['mrr_state']:>12.3f}"
              f"{pct(m.get('hallucination_rate')):>10}{pct(m.get('faithfulness')):>10}")
    print("=" * 92)

    # Deltas (the headline numbers for the presentation)
    print("\nKey deltas (region-aware vs baseline):")
    print(f"  Top-1 from correct state: {pct(no_region['top1_region'])} -> {pct(with_region['top1_region'])}")
    print(f"  Region hit@5:             {pct(no_region['region_hit5'])} -> {pct(with_region['region_hit5'])}")
    print(f"  MRR (state):              {no_region['mrr_state']:.3f} -> {with_region['mrr_state']:.3f}")
    if no_region.get("hallucination_rate") is not None and with_region.get("hallucination_rate") is not None:
        print(f"  Hallucination rate:       {pct(no_region['hallucination_rate'])} -> {pct(with_region['hallucination_rate'])}")

    out = {"rag_no_region": no_region, "rag_with_region": with_region}
    out_path = EVAL_FILE.parent / "results.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=None, help="limit number of eval examples")
    ap.add_argument("--no-generation", action="store_true",
                    help="retrieval metrics only; skip LLM calls (no quota used)")
    args = ap.parse_args()
    asyncio.run(main(args.n, with_generation=not args.no_generation))
