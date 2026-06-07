"""
RAG Engine - Retrieval Augmented Generation for document Q&A.
Uses ChromaDB for vector storage and Ollama/Gemma 3 for generation.
"""
import os, json, hashlib
from typing import List, Optional
import chromadb
from chromadb.config import Settings

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "uploads")
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

# Initialize ChromaDB
chroma_client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory=CHROMA_DIR,
    anonymized_telemetry=False
))

try:
    collection = chroma_client.get_or_create_collection(
        name="college_docs",
        metadata={"hnsw:space": "cosine"}
    )
except:
    collection = chroma_client.get_or_create_collection(name="college_docs")


def extract_text_from_pdf(filepath: str) -> str:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        return f"Error reading PDF: {e}"


def extract_text_from_docx(filepath: str) -> str:
    try:
        from docx import Document
        doc = Document(filepath)
        return "\n".join([p.text for p in doc.paragraphs]).strip()
    except Exception as e:
        return f"Error reading DOCX: {e}"


def extract_text(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(filepath)
    elif ext == ".docx":
        return extract_text_from_docx(filepath)
    elif ext in (".txt", ".md", ".csv"):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    return ""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    if not text:
        return []
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def add_document(filepath: str, filename: str, doc_type: str = "general") -> int:
    text = extract_text(filepath)
    if not text:
        return 0
    chunks = chunk_text(text)
    ids = []
    documents = []
    metadatas = []
    for i, chunk in enumerate(chunks):
        doc_id = hashlib.md5(f"{filename}_{i}".encode()).hexdigest()
        ids.append(doc_id)
        documents.append(chunk)
        metadatas.append({"source": filename, "chunk_index": i, "doc_type": doc_type})
    if ids:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return len(chunks)


def search_documents(query: str, n_results: int = 5) -> List[dict]:
    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        docs = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                dist = results["distances"][0][i] if results["distances"] else 0
                docs.append({"content": doc, "source": meta.get("source", "Unknown"), "relevance": round(1 - dist, 3)})
        return docs
    except Exception as e:
        print(f"Search error: {e}")
        return []


def get_doc_count() -> int:
    try:
        return collection.count()
    except:
        return 0
