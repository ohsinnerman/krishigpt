#!/usr/bin/env python3
"""
Cross-platform corpus + pincode downloader for KrishiGPT.

Strategy (resilient for a time-boxed build):
  1. Try to download real agricultural HTML pages (TNAU Agritech etc.).
  2. ALWAYS write a curated seed corpus of state-tagged docs so the demo
     works even if every network download fails.
  3. Try to download a pincode CSV; if it fails, the prefix fallback in
     pincode_mapper.py still resolves every pincode.

Usage: python scripts/download_corpus.py
"""
import os, sys
from pathlib import Path

# Make sibling modules (seed_docs.py) importable regardless of CWD.
sys.path.insert(0, str(Path(__file__).parent))

try:
    import httpx
except ImportError:
    httpx = None

ROOT = Path(__file__).parent.parent
CORPUS = ROOT / "backend" / "data" / "corpus"
PINCODE_CSV = ROOT / "backend" / "data" / "pincodes.csv"

CORPUS.mkdir(parents=True, exist_ok=True)

# Real sources to attempt (best-effort; failures are fine).
TNAU = "https://agritech.tnau.ac.in"
WEB_SOURCES = {
    "paddy_tnau_en.html": f"{TNAU}/agriculture/agri_cereals_paddy.html",
    "wheat_tnau_en.html": f"{TNAU}/agriculture/agri_cereals_wheat.html",
    "groundnut_tnau_en.html": f"{TNAU}/agriculture/agri_oilseeds_groundnut.html",
    "tomato_tnau_en.html": f"{TNAU}/horticulture/horti_vegetables_tomato.html",
    "sugarcane_tnau_en.html": f"{TNAU}/agriculture/agri_sugarcrops_sugarcane.html",
}

PINCODE_SOURCES = [
    "https://raw.githubusercontent.com/sanand0/pincode/master/pincode.csv",
    "https://raw.githubusercontent.com/datameet/Pincode/master/all_india_PO.csv",
]


def try_download(url: str, dest: Path) -> bool:
    if httpx is None:
        return False
    try:
        with httpx.Client(timeout=20, follow_redirects=True, verify=False) as client:
            r = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200 and len(r.content) > 500:
                dest.write_bytes(r.content)
                print(f"  OK   {dest.name}  ({len(r.content)} bytes)")
                return True
            print(f"  FAIL {dest.name}  (HTTP {r.status_code})")
    except Exception as e:
        print(f"  FAIL {dest.name}  ({type(e).__name__})")
    return False


def download_web_corpus():
    print("Downloading web corpus (best-effort)...")
    for name, url in WEB_SOURCES.items():
        try_download(url, CORPUS / name)


def write_seed_corpus():
    """Guaranteed curated docs so the demo always has region-tagged content.
    Filenames embed the state so the ingestion state-tagger picks them up."""
    print("Writing curated seed corpus...")
    for name, body in SEED_DOCS.items():
        (CORPUS / name).write_text(body, encoding="utf-8")
        print(f"  seed {name}")


def download_pincodes():
    print("Downloading pincode CSV (best-effort)...")
    for url in PINCODE_SOURCES:
        if try_download(url, PINCODE_CSV):
            return
    print("  No pincode CSV — prefix fallback in pincode_mapper.py will be used.")



# Curated, DETAILED seed documents live in scripts/seed_docs.py (kept separate so
# this orchestration file stays small). They are a prototype corpus modeled on ICAR
# Package of Practices + GoI scheme guidelines — see SOURCES.md for provenance.
from seed_docs import SEED_DOCS


if __name__ == "__main__":
    download_web_corpus()
    write_seed_corpus()
    download_pincodes()
    print("\nDone. Next: python scripts/build_index.py")
