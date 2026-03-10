import json
import os
import glob
import pdfplumber

RAG_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "rag_docs")
CHUNKS_OUTPUT = os.path.join(RAG_DOCS_DIR, "chunks.json")


def extract_pdf_text(pdf_path: str) -> str:
    """Extract all text from a PDF file, combining all pages into one string."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


def chunk_text(text: str, source_name: str, chunk_size: int = 512, overlap: int = 64) -> list:
    """
    Split text into overlapping chunks of chunk_size words with overlap words
    of overlap between consecutive chunks. Each chunk is a dict with:
      chunk_id, source, text, word_count
    """
    words = text.split()
    chunks = []
    start = 0
    idx = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text_str = " ".join(chunk_words)

        # Derive a short slug from the source name for the chunk_id prefix
        slug = "".join(c if c.isalnum() else "_" for c in source_name.lower())[:12].strip("_")
        chunk_id = f"{slug}_{idx:04d}"

        chunks.append({
            "chunk_id":   chunk_id,
            "source":     source_name,
            "text":       chunk_text_str,
            "word_count": len(chunk_words),
        })

        idx += 1
        start += chunk_size - overlap  # slide forward, keeping overlap words

    return chunks


if __name__ == "__main__":
    pdf_paths = glob.glob(os.path.join(RAG_DOCS_DIR, "*.pdf"))
    # Exclude Zone.Identifier sidecar files (Windows artifact, not real PDFs)
    pdf_paths = [p for p in pdf_paths if not p.endswith(":Zone.Identifier")]

    all_chunks = []

    for pdf_path in sorted(pdf_paths):
        source_name = os.path.basename(pdf_path)
        print(f"Processing: {source_name}")
        try:
            text = extract_pdf_text(pdf_path)
            chunks = chunk_text(text, source_name)
            all_chunks.extend(chunks)
            print(f"  → {len(chunks)} chunks ({len(text.split())} words total)")
        except Exception as e:
            print(f"  ✗ Failed: {e}")

    with open(CHUNKS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"\nTotal chunks: {len(all_chunks)}")
    print(f"Saved to: {CHUNKS_OUTPUT}")
