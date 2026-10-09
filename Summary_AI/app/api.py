"""
FastAPI Backend Application for MirAI Student Policy Advisor RAG System.
"""
import os
import time
import pandas as pd
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import settings
from app.models import (
    QueryRequest, QueryResponse, IngestResponse,
    EvaluationSummary, HealthStatus, EvalTestCaseResult
)
from app.ingestion import ingest_handbook, get_db_stats, ensure_handbook_exists
from app.rag_engine import query_policy_handbook
from app.evaluator import run_evaluation_suite

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes handbook PDF and ChromaDB on startup if needed."""
    try:
        ensure_handbook_exists()
        stats = get_db_stats()
        if stats.get("indexed_chunks", 0) == 0:
            print("ChromaDB is empty on startup. Triggering initial handbook ingestion...")
            ingest_handbook(force_reingest=False)
            print("Initial ingestion complete.")
    except Exception as e:
        print(f"Warning during startup initialization: {e}")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Authoritative, Strict Document-Grounded RAG API for MirAI School of Technology Student Policy Advisor.",
    lifespan=lifespan
)

# Enable CORS for Streamlit frontend and local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["General"])
async def root():
    """Root endpoint welcoming clients."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API v{settings.APP_VERSION}",
        "docs_url": "/docs",
        "health_check": "/health"
    }

@app.get("/health", response_model=HealthStatus, tags=["System"])
async def health_check():
    """Returns real-time system health, handbook presence, and vector database status."""
    handbook_path = settings.DATA_DIR / settings.HANDBOOK_FILENAME
    stats = get_db_stats()
    
    return HealthStatus(
        status="healthy" if stats.get("status") == "ready" else "initializing",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        handbook_present=handbook_path.exists(),
        handbook_path=str(handbook_path),
        vector_store_chunks=stats.get("indexed_chunks", 0),
        embedding_model=settings.EMBEDDING_MODEL,
        llm_model=settings.LLM_MODEL
    )

@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def query_policy(request: QueryRequest):
    """
    Submits a student query to the Strict Document-Grounded RAG Pipeline.
    Answers strictly using Mirai_SoT_Policy_Handbook_2026.pdf with citations.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Query question cannot be empty.")
    
    try:
        response = query_policy_handbook(
            question=request.question.strip(),
            top_k=request.top_k,
            use_multi_query=True
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query execution error: {str(e)}")

@app.post("/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def trigger_ingestion(force_reingest: bool = False):
    """
    Loads, chunks, embeds, and stores the official Policy Handbook in ChromaDB.
    """
    try:
        result = ingest_handbook(force_reingest=force_reingest)
        return IngestResponse(
            status=result["status"],
            document_path=result["document_path"],
            chunks_created=result["chunks_created"],
            collection_name=result["collection_name"],
            message=result["message"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Handbook ingestion failed: {str(e)}")

@app.post("/evaluate", response_model=EvaluationSummary, tags=["Evaluation"])
async def trigger_evaluation(use_multi_query: bool = False):
    """
    Runs the LLM-as-a-judge automated benchmark across policy and refusal test cases.
    Updates rag_eval_scores.csv.
    """
    try:
        summary = run_evaluation_suite(use_multi_query=use_multi_query)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation suite failed: {str(e)}")

@app.get("/eval-results", tags=["Evaluation"])
async def get_eval_results():
    """
    Retrieves the existing evaluation scores from rag_eval_scores.csv.
    """
    csv_path = settings.EVAL_CSV_PATH
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="No evaluation results found. Run /evaluate first.")
    
    try:
        df = pd.read_csv(csv_path)
        records = df.to_dict(orient="records")
        total = len(records)
        avg_faithfulness = round(df["faithfulness_score"].mean(), 3) if total else 0.0
        avg_relevance = round(df["answer_relevance_score"].mean(), 3) if total else 0.0
        avg_precision = round(df["context_precision_score"].mean(), 3) if total else 0.0
        groundedness_rate = round(df["grounded"].mean(), 3) if total else 0.0
        refusal_acc = round(df["refusal_accurate"].mean(), 3) if total else 0.0
        avg_latency = round(df["latency_seconds"].mean(), 3) if total else 0.0

        return {
            "total_tests": total,
            "avg_faithfulness": avg_faithfulness,
            "avg_relevance": avg_relevance,
            "avg_context_precision": avg_precision,
            "groundedness_rate": groundedness_rate,
            "refusal_accuracy": refusal_acc,
            "avg_latency": avg_latency,
            "csv_file": str(csv_path),
            "records": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read evaluation CSV: {str(e)}")

@app.get("/download-eval-csv", tags=["Evaluation"])
async def download_eval_csv():
    """Downloads the rag_eval_scores.csv file directly."""
    csv_path = settings.EVAL_CSV_PATH
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="rag_eval_scores.csv does not exist yet. Run /evaluate first.")
    return FileResponse(
        path=str(csv_path),
        filename="rag_eval_scores.csv",
        media_type="text/csv"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api:app", host="0.0.0.0", port=settings.FASTAPI_PORT, reload=False)
