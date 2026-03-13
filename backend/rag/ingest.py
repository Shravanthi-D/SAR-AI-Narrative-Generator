"""
RAG ingestion pipeline — extracts text from PDFs in rag_docs/, splits into
overlapping chunks, and writes them to rag_docs/chunks.json.

Run this once before running embedder.py.

Usage:
    python3 -m backend.rag.ingest
"""

import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv
import pdfplumber

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

_RAG_DOCS_DIR = Path(__file__).resolve().parents[2] / "rag_docs"
_CHUNKS_PATH = _RAG_DOCS_DIR / "chunks.json"
_CHUNK_SIZE = 500
_OVERLAP = 100


def _source_name(pdf_path: Path) -> str:
    name = pdf_path.stem.lower()
    if "fatf" in name:
        return "FATF Recommendation 29"
    if "pmla" in name:
        return "PMLA Section 12"
    return pdf_path.stem


def extract_text(pdf_path: Path) -> str:
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


def chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _OVERLAP) -> list:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks


def build_chunks(rag_docs_dir: Path = _RAG_DOCS_DIR) -> list:
    chunks = []
    chunk_index = 0
    for pdf_path in sorted(rag_docs_dir.glob("*.pdf")):
        source = _source_name(pdf_path)
        print(f"Extracting: {pdf_path.name}")
        text = extract_text(pdf_path)
        text = re.sub(r'\s+', ' ', text).strip()
        for chunk_text_str in chunk_text(text):
            chunks.append({
                "chunk_id": f"chunk_{chunk_index:04d}",
                "source": source,
                "text": chunk_text_str,
            })
            chunk_index += 1
        print(f"  → {chunk_index} total chunks so far")
    return chunks


if __name__ == "__main__":
    chunks = build_chunks()
    with open(_CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(chunks)} chunks to {_CHUNKS_PATH}")
