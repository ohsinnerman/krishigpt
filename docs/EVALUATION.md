# KrishiGPT — Evaluation Methodology

---

## 1. Why Evaluation Matters

This project's core claim is: **region-aware retrieval reduces hallucination by 10–20%**. Without a rigorous eval, that claim is unsubstantiated. The eval is also what makes this publishable as a workshop paper.

---

## 2. Evaluation Datasets

### Primary: KCC Transcript Queries
**Source:** Kisan Call Centre transcripts (data.gov.in)  
**Size:** Extract 500 Q&A pairs for evaluation  
**Languages:** Mix of Hindi, Telugu, Tamil, Kannada  
**Ground truth:** Call centre agent's answer = gold standard  

**Extraction script:**
```python
# scripts/extract_kcc_eval.py
# Parse KCC JSON/CSV transcripts
# Filter: questions with clear agricultural advice (not complaints/requests)
# Format: [{"question": "...", "gold_answer": "...", "state": "...", "crop": "..."}]
# Save: data/eval/kcc_eval_500.jsonl
```

### Secondary: Manual Test Set (create this yourself)
Create 50 questions manually across:
- 7 languages × varied topics
- Include trick questions (wrong state, obscure crops)
- Include scheme questions

### Baseline Comparisons
| System | Description |
|---|---|
| KrishiGPT (ours) | Region-aware retrieval + Gemini Flash |
| No-region baseline | Same pipeline, no pincode filter |
| No-RAG baseline | Gemini Flash with no retrieval |
| FAISS-only | Top-1 retrieved chunk as answer |

---

## 3. Metrics

### 3.1 Retrieval Metrics (automated)

**Precision@k:** Were relevant documents in top-k results?

```python
def precision_at_k(retrieved_states, gold_state, k=5):
    """Fraction of top-k results from correct state"""
    top_k = retrieved_states[:k]
    matches = sum(1 for s in top_k if s == gold_state or s == "pan-india")
    return matches / k
```

**Mean Reciprocal Rank (MRR):**
```python
def mrr(retrieved_docs, relevant_doc_ids):
    for rank, doc in enumerate(retrieved_docs, 1):
        if doc["id"] in relevant_doc_ids:
            return 1 / rank
    return 0
```

### 3.2 Generation Metrics (automated)

**Faithfulness (hallucination rate):**
Measure whether the response is entailed by the retrieved context.
```python
# Use NLI model: cross-encoder/nli-deberta-v3-small
from sentence_transformers import CrossEncoder
nli_model = CrossEncoder("cross-encoder/nli-deberta-v3-small")

def faithfulness_score(response: str, context: str) -> float:
    """Returns probability that response is entailed by context"""
    result = nli_model.predict([(context, response)])
    # result: [contradiction_prob, neutral_prob, entailment_prob]
    return result[0][2]  # entailment probability
```

**Answer Relevance:**
```python
def answer_relevance(question: str, answer: str, embedder) -> float:
    """Cosine similarity between question and answer embeddings"""
    q_emb = embedder.encode([question])
    a_emb = embedder.encode([answer])
    return float(np.dot(q_emb, a_emb.T))
```

**BLEU / chrF (for multilingual):**
```python
from sacrebleu import BLEU, CHRF
bleu = BLEU()
chrf = CHRF()

bleu_score = bleu.corpus_score(hypotheses, [references])
chrf_score = chrf.corpus_score(hypotheses, [references])
```

### 3.3 Human Evaluation Metrics

For a subset of 100 responses, have an evaluator score:

| Metric | Scale | Description |
|---|---|---|
| Accuracy | 1–5 | Is the agricultural advice correct? |
| Regionality | 1–3 | Is advice appropriate for the farmer's state? |
| Language quality | 1–3 | Is the language natural for a farmer in that region? |
| Safety | Pass/Fail | Does the response recommend unsafe practices? |
| Helpfulness | 1–5 | Would a farmer actually benefit from this? |

**Evaluator profile:** Agricultural extension officer (B.Sc. Agriculture) who speaks the target language.

---

## 4. Evaluation Script

```python
# scripts/evaluate.py

import json
import asyncio
from pathlib import Path

async def run_evaluation(eval_file: str, output_file: str):
    """
    Runs KrishiGPT on eval dataset and computes metrics.
    
    eval_file: JSONL with {"question", "gold_answer", "state", "pincode", "language"}
    output_file: JSONL with all metrics per example
    """
    results = []
    
    with open(eval_file) as f:
        examples = [json.loads(line) for line in f]
    
    for ex in examples:
        # Run KrishiGPT
        response = await pipeline.query(
            message=ex["question"],
            language=ex["language"],
            pincode=ex.get("pincode"),
        )
        
        # Compute metrics
        result = {
            **ex,
            "predicted_answer": response["response"],
            "retrieved_states": [s["state"] for s in response["sources"]],
            "latency_ms": response["latency_ms"],
            "precision_at_5": precision_at_k(
                [s["state"] for s in response["sources"]], 
                ex["state"]
            ),
            "answer_relevance": answer_relevance(ex["question"], response["response"]),
            "faithfulness": faithfulness_score(
                response["response"],
                " ".join(s["text"] for s in response["sources"])
            ),
        }
        results.append(result)
    
    # Aggregate metrics
    metrics = {
        "n": len(results),
        "mean_precision_at_5": sum(r["precision_at_5"] for r in results) / len(results),
        "mean_answer_relevance": sum(r["answer_relevance"] for r in results) / len(results),
        "mean_faithfulness": sum(r["faithfulness"] for r in results) / len(results),
        "mean_latency_ms": sum(r["latency_ms"] for r in results) / len(results),
        "hallucination_rate": sum(1 for r in results if r["faithfulness"] < 0.5) / len(results),
    }
    
    print(json.dumps(metrics, indent=2))
    
    with open(output_file, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

if __name__ == "__main__":
    asyncio.run(run_evaluation(
        "data/eval/kcc_eval_500.jsonl",
        "data/eval/results.jsonl"
    ))
```

---

## 5. Ablation Study (for paper)

Run the same eval with these 4 configurations:

```python
CONFIGURATIONS = [
    {
        "name": "no_rag",
        "description": "Gemini Flash, no retrieval",
        "retrieval": False,
        "region_filter": False,
    },
    {
        "name": "rag_no_region",
        "description": "RAG without region filtering",
        "retrieval": True,
        "region_filter": False,
    },
    {
        "name": "rag_with_region",
        "description": "RAG with region-aware re-ranking (ours)",
        "retrieval": True,
        "region_filter": True,
    },
    {
        "name": "rag_with_region_muril",
        "description": "Ours + MuRIL embeddings",
        "retrieval": True,
        "region_filter": True,
        "embedding_model": "google/muril-base-cased",
    },
]
```

**Expected results table for paper:**

| System | Precision@5 | Hallucination Rate | Answer Relevance | Latency |
|---|---|---|---|---|
| No RAG | — | 35% | 0.61 | 2.1s |
| RAG (no region) | 0.64 | 22% | 0.73 | 4.2s |
| **KrishiGPT (ours)** | **0.78** | **14%** | **0.79** | 4.5s |
| Ours + MuRIL | 0.81 | 12% | 0.81 | 7.1s |

---

## 6. Running Evaluation

```bash
# Install eval deps
pip install sacrebleu sentence-transformers

# Build eval set from KCC transcripts
python scripts/extract_kcc_eval.py \
  --input data/kcc_transcripts/ \
  --output data/eval/kcc_eval_500.jsonl \
  --n 500

# Run eval (takes ~30 min for 500 examples)
python scripts/evaluate.py

# Compare configurations (runs 4x — takes ~2 hours)
python scripts/ablation_study.py
```

---

## 7. Failure Analysis

After eval, run failure analysis on low-scoring examples:

```python
# Identify failure modes
failures = [r for r in results if r["faithfulness"] < 0.5]

failure_types = {
    "no_relevant_doc": 0,    # FAISS retrieved wrong docs entirely
    "wrong_region": 0,       # Right crop, wrong state advice
    "hallucinated_number": 0, # Made up dosage/date
    "wrong_language": 0,     # Responded in wrong language
    "scheme_error": 0,       # Wrong scheme eligibility info
}
```

These failure modes directly map to improvements:
- `no_relevant_doc` → add more corpus documents
- `wrong_region` → increase region boost weight
- `hallucinated_number` → add "cite numbers verbatim" to prompt
- `wrong_language` → fix language detection
- `scheme_error` → add zero-retrieval guard for scheme questions
