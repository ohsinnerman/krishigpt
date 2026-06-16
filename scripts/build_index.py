#!/usr/bin/env python3
"""Run this once after downloading corpus to build the FAISS index.

Writes index artifacts into backend/data/ so the backend (which runs from
backend/) finds them at the default relative paths.
"""
import os
from pathlib import Path
import sys

BACKEND = Path(__file__).parent.parent / "backend"
DATA = BACKEND / "data"

# Pin output paths BEFORE importing modules that read these at import time.
os.environ["FAISS_INDEX_PATH"] = str(DATA / "faiss.index")
os.environ["CHUNKS_PATH"] = str(DATA / "chunks.pkl")

sys.path.insert(0, str(BACKEND))

from data.ingest import run_ingestion

if __name__ == "__main__":
    run_ingestion(
        corpus_dir=str(DATA / "corpus"),
        output_dir=str(DATA),
    )
