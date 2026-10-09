"""
Document Ingestion Pipeline for MirAI Policy Handbook.
Uses PyPDFLoader, RecursiveCharacterTextSplitter, GoogleGenerativeAIEmbeddings, and ChromaDB.
"""
import os
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import settings
from app.pdf_generator import generate_handbook_pdf

def get_embeddings_model() -> GoogleGenerativeAIEmbeddings:
    """Returns GoogleGenerativeAIEmbeddings initialized with API key."""
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY is not configured in .env")
    
    return GoogleGenerativeAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        google_api_key=api_key
    )

def get_vector_store() -> Chroma:
    """Returns the persistent Chroma vector store instance."""
    embeddings = get_embeddings_model()
    return Chroma(
        collection_name=settings.COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(settings.CHROMA_DB_DIR)
    )

def ensure_handbook_exists() -> Path:
    """Ensures the handbook PDF exists in data/ directory."""
    handbook_path = settings.DATA_DIR / settings.HANDBOOK_FILENAME
    if not handbook_path.exists():
        generate_handbook_pdf(str(handbook_path))
    return handbook_path

def ingest_handbook(force_reingest: bool = False) -> Dict[str, Any]:
    """
    Ingests the official Mirai SoT Policy Handbook into ChromaDB.
    
    Steps:
    1. Verify handbook PDF existence.
    2. Load PDF using PyPDFLoader.
    3. Split into semantically coherent chunks using RecursiveCharacterTextSplitter.
    4. Store chunks with rich metadata in ChromaDB.
    """
    handbook_path = ensure_handbook_exists()
    
    # Check if collection already has documents and not force_reingest
    vector_store = get_vector_store()
    current_count = vector_store._collection.count()
    
    if current_count > 0 and not force_reingest:
        return {
            "status": "already_indexed",
            "document_path": str(handbook_path),
            "chunks_created": current_count,
            "collection_name": settings.COLLECTION_NAME,
            "message": f"ChromaDB already contains {current_count} indexed chunks from {settings.HANDBOOK_FILENAME}."
        }

    # If force re-indexing, reset/clear collection
    if force_reingest and current_count > 0:
        try:
            vector_store.delete_collection()
            vector_store = get_vector_store()
        except Exception:
            pass

    # 1. Load document with PyPDFLoader
    loader = PyPDFLoader(str(handbook_path))
    docs: List[Document] = loader.load()

    if not docs:
        raise ValueError(f"No pages could be extracted from {handbook_path}")

    # 2. Split with RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\nSECTION ", "\n\n", "\n• ", "\n", ". ", " ", ""]
    )
    
    chunks: List[Document] = []
    for doc in docs:
        page_num = doc.metadata.get("page", 0) + 1  # 1-indexed for citations
        page_chunks = text_splitter.split_documents([doc])
        for idx, chunk in enumerate(page_chunks):
            chunk.metadata["source"] = settings.HANDBOOK_FILENAME
            chunk.metadata["page"] = page_num
            chunk.metadata["chunk_id"] = f"p{page_num}_c{idx+1}"
            chunks.append(chunk)

    # 3. Embed and store in ChromaDB
    vector_store.add_documents(chunks)

    return {
        "status": "success",
        "document_path": str(handbook_path),
        "chunks_created": len(chunks),
        "collection_name": settings.COLLECTION_NAME,
        "message": f"Successfully ingested {len(chunks)} chunks from {settings.HANDBOOK_FILENAME} into ChromaDB."
    }

def get_db_stats() -> Dict[str, Any]:
    """Returns vector store statistics."""
    try:
        vs = get_vector_store()
        count = vs._collection.count()
        return {
            "indexed_chunks": count,
            "collection_name": settings.COLLECTION_NAME,
            "status": "ready" if count > 0 else "empty"
        }
    except Exception as e:
        return {
            "indexed_chunks": 0,
            "collection_name": settings.COLLECTION_NAME,
            "status": f"error: {str(e)}"
        }

if __name__ == "__main__":
    result = ingest_handbook(force_reingest=True)
    print(result)
