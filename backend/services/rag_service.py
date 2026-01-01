"""
RAG (Retrieval Augmented Generation) Service
Handles PDF ingestion, text chunking, embeddings, vector storage (FAISS), and retrieval
"""

import os
import pickle
import random
from typing import List, Dict

import numpy as np
import faiss
from PyPDF2 import PdfReader

# ---------------- CONFIG ----------------

UPLOAD_DIR = "uploads"
VECTOR_DB_DIR = "vector_db"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_DIM = 1536

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTOR_DB_DIR, exist_ok=True)

# ---------------- OPENAI CLIENT ----------------

_openai_client = None

def get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI()
    return _openai_client


# ---------------- RAG SERVICE ----------------

class RAGService:
    def __init__(self):
        self.index_path = os.path.join(VECTOR_DB_DIR, "faiss_index.bin")
        self.metadata_path = os.path.join(VECTOR_DB_DIR, "metadata.pkl")

        self.index = None
        self.metadata: List[Dict] = []

        self._load_or_create_index()

    # ---------- FAISS SETUP ----------

    def _load_or_create_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, "rb") as f:
                    self.metadata = pickle.load(f)
                print("✅ FAISS index loaded")
                return
            except Exception as e:
                print("⚠️ Failed to load FAISS index:", e)

        self._create_new_index()

    def _create_new_index(self):
        self.index = faiss.IndexFlatL2(EMBEDDING_DIM)
        self.metadata = []
        print("🆕 New FAISS index created")

    def _save_index(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)

    # ---------- PDF TEXT EXTRACTION ----------

    def extract_text_from_pdf(self, file_path: str) -> str:
        text = ""
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

            print(f"📄 Extracted text length: {len(text)}")
            return text

        except Exception as e:
            print("❌ PDF extraction error:", e)
            return ""

    # ---------- CHUNKING ----------

    def chunk_text(self, text: str) -> List[str]:
        chunks = []
        text = text.strip()

        if not text:
            return chunks

        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + CHUNK_SIZE

            if end < text_len:
                split_point = max(
                    text.rfind(".", start, end),
                    text.rfind("\n", start, end)
                )
                if split_point > start:
                    end = split_point + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - CHUNK_OVERLAP
            if start < 0 or start >= text_len:
                break

        return chunks

    # ---------- EMBEDDINGS ----------

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        try:
            client = get_openai_client()
            vectors = []

            for i in range(0, len(texts), 20):
                batch = texts[i:i + 20]
                response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=batch
                )
                for item in response.data:
                    vectors.append(item.embedding)

            return np.array(vectors, dtype="float32")

        except Exception as e:
            print("⚠️ Embedding error:", e)
            return np.array([])

    # ---------- INGEST DOCUMENT ----------

    def ingest_document(
        self,
        file_path: str,
        subject_id: int,
        unit_id: int,
        document_id: int
    ) -> int:

        text = self.extract_text_from_pdf(file_path)
        if not text.strip():
            print("❌ No text extracted from PDF")
            return 0

        chunks = self.chunk_text(text)
        print(f"🧩 Chunks created: {len(chunks)}")

        if not chunks:
            return 0

        embeddings = self.get_embeddings(chunks)

        start_idx = self.index.ntotal

        # --- If embeddings FAIL, still save chunks ---
        if embeddings is None or len(embeddings) == 0:
            print("⚠️ Embeddings failed – saving text only")

            for i, chunk in enumerate(chunks):
                self.metadata.append({
                    "chunk_id": start_idx + i,
                    "subject_id": subject_id,
                    "unit_id": unit_id,
                    "document_id": document_id,
                    "text": chunk
                })

            self._save_index()
            return len(chunks)

        # --- Normal path ---
        self.index.add(embeddings)

        for i, chunk in enumerate(chunks):
            self.metadata.append({
                "chunk_id": start_idx + i,
                "subject_id": subject_id,
                "unit_id": unit_id,
                "document_id": document_id,
                "text": chunk
            })

        self._save_index()
        return len(chunks)

    # ---------- RETRIEVAL ----------

    def retrieve_context(
        self,
        subject_id: int,
        unit_id: int,
        query: str = "",
        top_k: int = 5
    ) -> List[Dict]:

        filtered = [
            m for m in self.metadata
            if m["subject_id"] == subject_id and m["unit_id"] == unit_id
        ]

        if not filtered:
            return []

        if query and self.index.ntotal > 0:
            q_emb = self.get_embeddings([query])
            if len(q_emb) > 0:
                k = min(top_k * 3, self.index.ntotal)
                _, indices = self.index.search(q_emb, k)

                results = []
                valid_ids = {m["chunk_id"] for m in filtered}

                for idx in indices[0]:
                    if idx in valid_ids:
                        for m in filtered:
                            if m["chunk_id"] == idx:
                                results.append(m)
                                break
                    if len(results) >= top_k:
                        break

                return results[:top_k]

        return random.sample(filtered, min(top_k, len(filtered)))


# ---------- SINGLETON ----------

rag_service = RAGService()
