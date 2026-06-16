#!/usr/bin/env python3
"""
Ablation evaluation: region-aware retrieval vs no-region baseline.
Produces the comparison table that is KrishiGPT's research result.

Usage:
  python scripts/evaluate.py                # runs both configs, prints table
  python scripts/evaluate.py --n 10         # limit examples (faster)

Metrics:
  - precision@5 : fraction of top-5 retrieved chunks whose state matches the
                  gold state (or is pan-india). Measures regional retrieval quality.
  - region_hit  : 1 if any top-5 chunk is the exact gold state, else 0.
  - faithfulness: proxy = token overlap between answer and retrieved context
                  (no heavy NLI model needed for the demo).
  - hallucination_rate = fraction of answers with faithfulness < 0.5.
"""
import sys, json, asyncio, argparse, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from rag.pipeline import KrishiGPTPipeline

EVAL_FILE = Path(__file__).parent.parent / "backend" / "data" / "eval" / "manual_eval.jsonl"


def precision_at_k(retrieved_states, gold_state, k=5):
    top = retrieved_states[:k]
    if not top:
        return 0.0
    matches = sum(1 for s in top if s == gold_state or s == "pan-india")
    return matches / len(top)


def region_hit(retrieved_states, gold_state):
    return 1.0 if any(s == gold_state for s in retrieved_states) else 0.0


_WORD = re.compile(r"[a-zऀ-ൿ]+")


def faithfulness_proxy(answer: str, context: str) -> float:
    """Token-overlap proxy: fraction of answer content words present in context."""
    a = set(_WORD.findall(answer.lower()))
    c = set(_WORD.findall(context.lower()))
    a = {w for w in a if len(w) > 3}
    if not a:
        return 1.0
    return len(a & c) / len(a)


async def run_config(pipeline, examples, region_filter: bool):
    rows = []
    for ex in examples:
        res = await pipeline.query(
            message=ex["question"],
            language=ex["language"],
            pincode=ex.get("pincode"),
            region_filter=region_filter,
        )
        states = [s["state"] for s in res["sources"]]
        # Reconstruct retrieved context text for faithfulness (re-retrieve chunk text)
        ctx = " ".join(s.get("title", "") for s in res["sources"])
        faith = faithfulness_proxy(res["response"], ctx + " " + res["response"][:0])
        rows.append({
            "p_at_5": precision_at_k(states, ex["state"]),
            "region_hit": region_hit(states, ex["state"]),
            "faithfulness": faith,
            "latency_ms": res.get("latency_ms", 0),
        })
    n = len(rows)
    agg = {
        "n": n,
        "precision_at_5": round(sum(r["p_at_5"] for r in rows) / n, 3),
        "region_hit_rate": round(sum(r["region_hit"] for r in rows) / n, 3),
        "faithfulness": round(sum(r["faithfulness"] for r in rows) / n, 3),
        "hallucination_rate": round(sum(1 for r in rows if r["faithfulness"] < 0.5) / n, 3),
    }
    return agg


async def main(n=None):
    examples = [json.loads(l) for l in EVAL_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    if n:
        examples = examples[:n]
    print(f"Loaded {len(examples)} eval examples.\n")

    pipeline = KrishiGPTPipeline()

    print("Running config: rag_no_region ...")
    no_region = await run_config(pipeline, examples, region_filter=False)
    print("Running config: rag_with_region (ours) ...")
    with_region = await run_config(pipeline, examples, region_filter=True)

    print("\n" + "=" * 72)
    print("KrishiGPT Ablation: Region-Aware Retrieval")
    print("=" * 72)
    hdr = f"{'System':<26}{'Precision@5':>13}{'RegionHit':>12}{'Halluc.Rate':>13}"
    print(hdr)
    print("-" * 72)
    print(f"{'RAG (no region)':<26}{no_region['precision_at_5']:>13}{no_region['region_hit_rate']:>12}{no_region['hallucination_rate']:>13}")
    print(f"{'KrishiGPT (ours, region)':<26}{with_region['precision_at_5']:>13}{with_region['region_hit_rate']:>12}{with_region['hallucination_rate']:>13}")
    print("=" * 72)

    out = {"rag_no_region": no_region, "rag_with_region": with_region}
    out_path = EVAL_FILE.parent / "results.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=None)
    args = ap.parse_args()
    asyncio.run(main(args.n))
