# KrishiGPT — Data Sources & Corpus Strategy

---

## 1. Corpus Overview

The KrishiGPT knowledge base is built from three tiers of agricultural documents, each with different coverage, format, and reliability characteristics.

---

## 2. Document Tiers

### Tier 1: ICAR Package of Practices (Primary Source)
**What:** Crop-specific production guides authored by Indian Council of Agricultural Research  
**Format:** PDF (text-based, generally good quality)  
**Coverage:** ~80 major crops × major producing states  
**Language:** English (primary), some Hindi  
**URL patterns:**
```
https://www.icar.org.in/content/package-practices
https://krishi.icar.gov.in/jspui/handle/...
```

**Filename convention (adopt this for tagging):**
```
icar_pop_{crop}_{state}.pdf
icar_pop_paddy_karnataka.pdf
icar_pop_wheat_punjab.pdf
icar_pop_cotton_gujarat.pdf
```

**Key documents to prioritize (by farmer population):**
- Paddy/Rice: UP, WB, Punjab, AP, Telangana, Karnataka, Tamil Nadu
- Wheat: Punjab, Haryana, UP, MP
- Cotton: Gujarat, Maharashtra, AP, Telangana
- Sugarcane: UP, Maharashtra, Karnataka
- Groundnut: Gujarat, AP, Tamil Nadu
- Pulses (tur/moong/urad): MP, Maharashtra, Rajasthan
- Vegetables: Karnataka, Maharashtra, UP (high value, high questions)
- Banana: Tamil Nadu, AP, Maharashtra

### Tier 2: KVK Booklets and State Agriculture Dept Documents
**What:** Krishi Vigyan Kendra (Farm Science Centre) extension materials — more localized, often bilingual  
**Format:** PDF (mixed quality, some scanned)  
**Coverage:** District-level specifics; pest calendars; local variety names  
**Sources:**
```
https://agritech.tnau.ac.in/                    (Tamil Nadu AG Uni — excellent)
https://icar-nrri.res.in/                       (Rice Research Institute)
https://icar-atari.res.in/                      (Zone-specific KVK outputs)
https://krishijagran.com/farm-activities/        (Hindi advisory content)
```

### Tier 3: Government Scheme Documents
**What:** PMFBY, PMKISAN, KCC official guidelines  
**Format:** PDF + HTML (official notifications)  
**Coverage:** National, but with state-level amendments  
**Sources:**
```
PMFBY:   https://pmfby.gov.in/pdf/Guidelines/...
PMKISAN: https://pmkisan.gov.in/Documents/...
KCC:     https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx
         https://nabard.org/auth/writereaddata/tender/...
```

**Important:** Tag ALL scheme documents as `state: "pan-india"` + specific state amendment if applicable.

---

## 3. Download Script

`scripts/download_corpus.sh` should:

```bash
#!/bin/bash
# Creates data/corpus/ with all PDFs

mkdir -p data/corpus/{icar_pop,kvk,schemes}

# ── ICAR PoPs (high priority) ──────────────────────────────────────────────
# These URLs need to be scraped from ICAR portal (or use these direct links)
# Fallback: agritech.tnau.ac.in has many PoPs as HTML — scrape to PDF

ICAR_BASE="https://agritech.tnau.ac.in"

declare -A CROPS=(
  ["paddy"]="$ICAR_BASE/crop_production/cpu_rice.html"
  ["wheat"]="$ICAR_BASE/crop_production/cpu_wheat.html"
  ["cotton"]="$ICAR_BASE/crop_production/cpu_cotton.html"
  # add more
)

for crop in "${!CROPS[@]}"; do
  wget -q "${CROPS[$crop]}" -O "data/corpus/icar_pop/${crop}_tnau.html"
done

# ── Scheme PDFs ─────────────────────────────────────────────────────────────
wget -q "https://pmfby.gov.in/pdf/Guidelines/Revised_Operational_Guidelines_PMFBY.pdf" \
     -O "data/corpus/schemes/pmfby_guidelines.pdf"

wget -q "https://pmkisan.gov.in/Documents/Pradhan_Mantri_Kisan_Samman_Nidhi.pdf" \
     -O "data/corpus/schemes/pmkisan_guidelines.pdf"

echo "Download complete. Run: python scripts/build_index.py"
```

---

## 4. Chunking Strategy

### Parameters (tune these if retrieval quality is poor)
```python
CHUNK_SIZE = 512        # tokens (approx 400 words)
CHUNK_OVERLAP = 64      # tokens
SEPARATORS = [
    "\n\n",             # paragraph break (highest priority)
    "\n",               # line break
    ". ",               # sentence end
    ", ",               # clause
    " ",                # word
]
```

### Special handling
- **Tables:** Extract as structured text. Format: "Crop: Paddy. Nitrogen: 120 kg/ha. Phosphorus: 60 kg/ha. Potassium: 60 kg/ha."
- **Headers:** Always include the section header in the chunk that follows it (prepend to next chunk if it fits)
- **Captions:** Include figure/table captions with the chunk immediately above
- **Page numbers and headers/footers:** Strip them before chunking

### Minimum chunk size
Discard chunks with fewer than 100 characters — these are usually headers, page numbers, or extraction artifacts.

---

## 5. Metadata Tagging Strategy

Every chunk must have this metadata dict:
```python
{
    "chunk_id": str,           # UUID
    "source_file": str,        # original filename
    "source_title": str,       # document title (extracted from PDF metadata or filename)
    "state": str,              # one of 28 states, 8 UTs, or "pan-india"
    "agro_zone": str,          # see zone list below
    "crop": str | None,        # "paddy", "wheat", "cotton", etc. or None for scheme docs
    "topic": str,              # see topic taxonomy below
    "language": str,           # "en", "hi", "kn", etc.
    "page_number": int,
    "chunk_index": int,        # position within document
    "text": str,               # the actual chunk text
}
```

### State tagging (from filename)
```python
STATE_KEYWORDS = {
    "karnataka": "Karnataka",
    "kk": "Karnataka",
    "tamilnadu": "Tamil Nadu",
    "tn": "Tamil Nadu",
    "andhra": "Andhra Pradesh",
    "ap": "Andhra Pradesh",
    "telangana": "Telangana",
    "ts": "Telangana",
    "maharashtra": "Maharashtra",
    "mh": "Maharashtra",
    "gujarat": "Gujarat",
    "gj": "Gujarat",
    "punjab": "Punjab",
    "pb": "Punjab",
    "haryana": "Haryana",
    "hr": "Haryana",
    "uttarpradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    "madhyapradesh": "Madhya Pradesh",
    "mp": "Madhya Pradesh",
    "rajasthan": "Rajasthan",
    "rj": "Rajasthan",
    "westbengal": "West Bengal",
    "wb": "West Bengal",
    "odisha": "Odisha",
    "od": "Odisha",
    "assam": "Assam",
    "as": "Assam",
    # ... full list
}

# If no state keyword found → "pan-india"
```

### Agro-climatic zone mapping
```python
AGRO_ZONES = {
    "Punjab": "IGP-Northwest",
    "Haryana": "IGP-Northwest",
    "Uttarakhand": "IGP-Northwest",
    "Delhi": "IGP-Northwest",
    "Himachal Pradesh": "Western Himalaya",
    "Jammu & Kashmir": "Western Himalaya",
    "Uttar Pradesh": "IGP-Central",
    "Bihar": "IGP-East",
    "West Bengal": "Eastern",
    "Jharkhand": "Eastern",
    "Odisha": "Eastern",
    "Chhattisgarh": "Eastern",
    "Assam": "Northeast",
    "Meghalaya": "Northeast",
    "Manipur": "Northeast",
    "Nagaland": "Northeast",
    "Arunachal Pradesh": "Northeast",
    "Mizoram": "Northeast",
    "Tripura": "Northeast",
    "Sikkim": "Northeast",
    "Madhya Pradesh": "Central",
    "Maharashtra": "Deccan",
    "Gujarat": "Arid-Semi",
    "Rajasthan": "Arid",
    "Karnataka": "Deccan-South",
    "Andhra Pradesh": "Deccan-South",
    "Telangana": "Deccan-South",
    "Tamil Nadu": "South",
    "Kerala": "South-Coastal",
    "Goa": "South-Coastal",
}
```

### Topic taxonomy
```python
TOPIC_KEYWORDS = {
    "pest": ["pest", "insect", "aphid", "thrips", "borer", "whitefly", "infestation", "कीट", "কীট"],
    "disease": ["disease", "blight", "rust", "wilt", "rot", "fungal", "bacterial", "virus", "रोग"],
    "fertilizer": ["fertilizer", "nutrient", "nitrogen", "phosphorus", "urea", "DAP", "potassium", "खाद", "उर्वरक"],
    "irrigation": ["irrigation", "water", "drip", "sprinkler", "flood", "सिंचाई"],
    "harvest": ["harvest", "yield", "storage", "post-harvest", "कटाई", "उत्पादन"],
    "variety": ["variety", "cultivar", "hybrid", "seed", "किस्म", "बीज"],
    "scheme": ["PMFBY", "PMKISAN", "KCC", "insurance", "credit", "subsidy", "yojana", "योजना"],
    "soil": ["soil", "pH", "organic matter", "texture", "drainage", "मिट्टी"],
    "market": ["price", "mandi", "MSP", "market", "sell", "बाज़ार", "मंडी"],
    "general": [],  # fallback
}
```

---

## 6. Evaluation Dataset

### Primary Eval: Kisan Call Centre Transcripts
**Source:** data.gov.in — "Kisan Call Centre Farmer Queries" dataset  
**Size:** ~6.7 GB (conversation transcripts, 2019–2023)  
**Languages:** Hindi (70%), Telugu (10%), Tamil (8%), Kannada (5%), others  
**Use:** Extract question-answer pairs; test if KrishiGPT retrieves the right document  

**Download:**
```bash
# Register at data.gov.in and download via API:
curl "https://data.gov.in/api/datastore/resource.json?resource_id=XXXX&api-key=YOUR_KEY" \
     -o kcc_transcripts.json
```

### Eval Metrics to Compute
```python
# For each (question, expected_answer) pair:
# 1. Retrieval precision@5: was the right document in top 5?
# 2. Answer faithfulness: does response contradict the retrieved context?
# 3. Answer relevance: cosine sim between question and response embeddings
# 4. Regional accuracy: if question specifies a state, is response state-appropriate?
# 5. Language fidelity: is response in the correct language?
```

### Baseline for Paper
- **Non-region-aware baseline:** Same pipeline but no pincode/state filtering
- **Region-aware (ours):** With pincode → state → re-ranking
- **Expected delta:** 10–20% improvement in retrieval precision and hallucination rate (per AgriRegion paper)

---

## 7. Corpus Maintenance

- Re-ingest quarterly (ICAR updates PoPs seasonally)
- Add new scheme notifications within 1 week of government release
- Log all "I don't know" responses — if recurring, that's a corpus gap
- Community contribution process: PR with new PDF + auto-ingest CI action
