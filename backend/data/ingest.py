"""
Ingestion pipeline: PDF/HTML/TXT documents -> text -> chunks -> embeddings -> FAISS index.
Usage: python -m data.ingest --corpus-dir data/corpus --output-dir data
"""
import os, sys, argparse, re, uuid
from pathlib import Path

from langdetect import detect, LangDetectException
# NOTE: PyMuPDF (`fitz`) is imported lazily inside extract_text_from_pdf() so the
# ingester works without it when the corpus is HTML/TXT only (e.g. the seed docs).

# Add parent (backend/) to path so `rag` and `data` import cleanly
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
}

TOPIC_KEYWORDS = {
    "pest": ["pest", "insect", "aphid", "thrips", "borer", "whitefly", "mite", "weevil"],
    "disease": ["disease", "blight", "rust", "wilt", "rot", "fungal", "bacterial", "virus", "blast"],
    "fertilizer": ["fertilizer", "nutrient", "nitrogen", "phosphorus", "urea", "dap", "potassium", "manure"],
    "irrigation": ["irrigation", "water management", "drip", "sprinkler", "flood irrigation"],
    "harvest": ["harvest", "harvesting", "yield", "storage", "post-harvest", "threshing"],
    "variety": ["variety", "cultivar", "hybrid", "seed selection", "sowing"],
    "scheme": ["pmfby", "pmkisan", "kcc", "insurance", "credit", "loan", "subsidy"],
    "soil": ["soil", "ph", "organic matter", "soil health", "drainage"],
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
    import fitz  # PyMuPDF — only needed when a real PDF is in the corpus
    doc = fitz.open(path)
    pages = []
    for page in doc:
        text = page.get_text("text")
        if len(text.strip()) < 50:
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
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()

    if len(text) <= chunk_size:
        return [text] if len(text) > 100 else []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
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
        if keyword in fn_lower:
            return state
    text_lower = text[:500].lower()
    for keyword, state in STATE_KEYWORDS.items():
        if keyword in text_lower:
            return state
    return "pan-india"


def detect_topic(text: str) -> str:
    text_lower = text.lower()
    scores = {t: sum(1 for kw in kws if kw in text_lower) for t, kws in TOPIC_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def detect_language(text: str) -> str:
    try:
        return detect(text[:200])
    except LangDetectException:
        return "en"


def detect_crop(filename: str, text: str):
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

    state = detect_state(path.name, text)
    topic = detect_topic(text)
    language = detect_language(text)
    crop = detect_crop(path.name, text)
    agro_zone = AGRO_ZONES.get(state, "pan-india")

    first_line = text.split("\n")[0][:100].strip()
    title = first_line if len(first_line) > 10 else path.stem.replace("_", " ").title()

    raw_chunks = chunk_text(text)

    chunks = []
    for i, chunk_val in enumerate(raw_chunks):
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
            "text": chunk_val,
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
        all_chunks.extend(ingest_file(str(f)))

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
    from collections import Counter
    states = Counter(c["state"] for c in all_chunks)
    print("State distribution:")
    for state, count in states.most_common(10):
        print(f"  {state}: {count} chunks")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", default="data/corpus")
    parser.add_argument("--output-dir", default="data")
    args = parser.parse_args()
    run_ingestion(args.corpus_dir, args.output_dir)
