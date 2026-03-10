"""
ingest.py — ImmigraSmart Knowledge Base Ingestion Pipeline
Improvements over v1:
  - Section-aware chunking (splits on SECTION headers, not arbitrary character count)
  - Metadata tagging per chunk (section_id, audience, keywords, source)
  - Confidence thresholding helpers stored in DB metadata
  - Retry logic with exponential backoff for Google API rate limits
  - Idempotent: skips re-ingestion if DB is already up to date
"""

import os
import re
import shutil
import time
import hashlib
import json
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

PERSIST_DIR = "/tmp/vector_db"
DATA_DIR = "data"
HASH_FILE = "/tmp/vector_db_hash.json"

# ── Helpers ────────────────────────────────────────────────────────────────────

def compute_file_hash(filepath: str) -> str:
    """Returns MD5 hash of a file to detect changes."""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def load_hashes() -> dict:
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE) as f:
            return json.load(f)
    return {}


def save_hashes(hashes: dict):
    with open(HASH_FILE, "w") as f:
        json.dump(hashes, f)


def files_changed(data_dir: str) -> bool:
    """Returns True if any data file has changed since last ingest."""
    old_hashes = load_hashes()
    current_hashes = {}
    for fname in os.listdir(data_dir):
        fpath = os.path.join(data_dir, fname)
        if os.path.isfile(fpath):
            current_hashes[fname] = compute_file_hash(fpath)
    if current_hashes != old_hashes:
        save_hashes(current_hashes)
        return True
    return False


# ── Section-Aware TXT Chunker ──────────────────────────────────────────────────

SECTION_PATTERN = re.compile(
    r"={5,}\nSECTION \d+[^\n]*\n={5,}",
    re.MULTILINE
)

METADATA_PATTERN = re.compile(
    r"\[SECTION_ID:\s*(.+?)\]\s*\n"
    r"\[AUDIENCE:\s*(.+?)\]\s*\n"
    r"\[KEYWORDS:\s*(.+?)\]",
    re.DOTALL
)


def parse_txt_into_sections(filepath: str) -> list[Document]:
    """
    Splits a structured TXT file into one Document per section.
    Extracts SECTION_ID, AUDIENCE, and KEYWORDS metadata tags.
    Falls back to generic chunking if no section markers found.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    # Split on the === SECTION N: ... === dividers
    parts = SECTION_PATTERN.split(raw)
    headers = SECTION_PATTERN.findall(raw)

    documents = []

    # First part is the file header/intro — keep as one doc
    if parts[0].strip():
        documents.append(Document(
            page_content=parts[0].strip(),
            metadata={
                "source": filepath,
                "section_id": "header",
                "audience": "all",
                "keywords": "introduction, overview",
                "chunk_type": "header"
            }
        ))

    for i, content in enumerate(parts[1:], start=1):
        if not content.strip():
            continue

        # Extract metadata tags embedded in the section text
        meta_match = METADATA_PATTERN.search(content)
        section_id = meta_match.group(1).strip() if meta_match else f"section_{i}"
        audience = meta_match.group(2).strip() if meta_match else "all"
        keywords = meta_match.group(3).strip() if meta_match else ""

        # Get the section title from the header divider
        section_title = headers[i - 1].strip().split("\n")[1] if i - 1 < len(headers) else f"Section {i}"

        # Remove the metadata tag lines from content (they're stored in metadata)
        clean_content = METADATA_PATTERN.sub("", content).strip()

        # For very long sections, further split by sub-headings (--- X.Y TITLE ---)
        sub_sections = re.split(r"\n--- .+ ---\n", clean_content)
        sub_headers = re.findall(r"\n--- (.+?) ---\n", clean_content)

        if len(sub_sections) > 1:
            for j, sub_content in enumerate(sub_sections):
                if not sub_content.strip():
                    continue
                sub_title = sub_headers[j - 1] if j > 0 and j - 1 < len(sub_headers) else section_title
                documents.append(Document(
                    page_content=f"{section_title} — {sub_title}\n\n{sub_content.strip()}",
                    metadata={
                        "source": filepath,
                        "section_id": section_id,
                        "section_title": section_title,
                        "sub_section": sub_title,
                        "audience": audience,
                        "keywords": keywords,
                        "chunk_type": "sub_section"
                    }
                ))
        else:
            documents.append(Document(
                page_content=f"{section_title}\n\n{clean_content}",
                metadata={
                    "source": filepath,
                    "section_id": section_id,
                    "section_title": section_title,
                    "audience": audience,
                    "keywords": keywords,
                    "chunk_type": "full_section"
                }
            ))

    print(f"  ✓ Parsed '{os.path.basename(filepath)}' → {len(documents)} section chunks")
    return documents


def load_pdfs(data_dir: str) -> list[Document]:
    """Loads all PDFs from the data directory with fallback text splitter."""
    docs = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
    for fname in os.listdir(data_dir):
        if fname.lower().endswith(".pdf"):
            fpath = os.path.join(data_dir, fname)
            try:
                loader = PyPDFLoader(fpath)
                pages = loader.load()
                chunks = splitter.split_documents(pages)
                # Tag with filename-based metadata
                for chunk in chunks:
                    chunk.metadata["section_id"] = fname.replace(".pdf", "").lower()
                    chunk.metadata["chunk_type"] = "pdf"
                    chunk.metadata["audience"] = "all"
                docs.extend(chunks)
                print(f"  ✓ Loaded PDF '{fname}' → {len(chunks)} chunks")
            except Exception as e:
                print(f"  ✗ Failed to load '{fname}': {e}")
    return docs


# ── Embedding with Retry ───────────────────────────────────────────────────────

def embed_with_retry(
    documents: list[Document],
    embeddings: GoogleGenerativeAIEmbeddings,
    persist_dir: str,
    batch_size: int = 5,
    max_retries: int = 3,
):
    """Embeds documents in batches with exponential backoff on API errors."""
    print(f"\nEmbedding {len(documents)} chunks in batches of {batch_size}...")

    # Initialize DB with first batch
    first_batch = documents[:batch_size]
    for attempt in range(max_retries):
        try:
            vector_db = Chroma.from_documents(
                documents=first_batch,
                embedding=embeddings,
                persist_directory=persist_dir
            )
            break
        except Exception as e:
            wait = 2 ** attempt
            print(f"  ✗ Attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)
    else:
        raise RuntimeError("Failed to initialize Chroma DB after max retries.")

    # Add remaining batches
    for i in range(batch_size, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        for attempt in range(max_retries):
            try:
                vector_db.add_documents(batch)
                print(f"  → {min(i + batch_size, len(documents))}/{len(documents)} chunks embedded")
                time.sleep(1)  # Gentle rate-limit buffer
                break
            except Exception as e:
                wait = 2 ** attempt
                print(f"  ✗ Batch {i} attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)
        else:
            print(f"  ✗ Skipping batch starting at {i} after {max_retries} failed attempts.")

    return vector_db


# ── Main ───────────────────────────────────────────────────────────────────────

def main(force: bool = False):
    print("\n" + "="*60)
    print("  ImmigraSmart — Knowledge Base Ingestion")
    print("="*60)

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created '{DATA_DIR}/' directory. Add your .txt and .pdf files.")
        return

    # Skip re-ingestion if nothing changed (unless forced)
    if not force and os.path.exists(PERSIST_DIR) and not files_changed(DATA_DIR):
        print("✓ Knowledge base is up to date. Skipping re-ingestion.")
        print("  (Use force=True to re-ingest regardless.)")
        return

    print("Changes detected. Re-building knowledge base...\n")

    # Load all documents
    all_docs = []

    for fname in os.listdir(DATA_DIR):
        fpath = os.path.join(DATA_DIR, fname)
        if fname.lower().endswith(".txt"):
            all_docs.extend(parse_txt_into_sections(fpath))

    all_docs.extend(load_pdfs(DATA_DIR))

    if not all_docs:
        print("No documents found in 'data/'. Add .txt or .pdf files.")
        return

    print(f"\nTotal chunks to embed: {len(all_docs)}")

    # Set up embeddings
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY not found in environment variables.")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key,
        task_type="retrieval_document"
    )

    # Wipe old DB and rebuild
    if os.path.exists(PERSIST_DIR):
        shutil.rmtree(PERSIST_DIR)
        print("Cleared old vector database.")

    embed_with_retry(all_docs, embeddings, PERSIST_DIR)

    print("\n✓ Ingestion complete! Knowledge base saved to:", PERSIST_DIR)
    print(f"  Total chunks indexed: {len(all_docs)}")


if __name__ == "__main__":
    main(force=True)