"""
Pydantic Schemas for MirAI Student Policy Advisor.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SourceCitation(BaseModel):
    source: str = Field(..., description="Name of source document")
    page: int = Field(..., description="Page number of the citation")
    snippet: str = Field(..., description="Relevant text snippet from chunk")
    chunk_id: Optional[str] = Field(None, description="Unique chunk identifier")

class QueryRequest(BaseModel):
    question: str = Field(..., description="Student inquiry regarding MirAI policies")
    top_k: Optional[int] = Field(None, description="Optional override for top_k documents")

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceCitation]
    retrieved_contexts: List[str]
    expanded_queries: List[str]
    latency_seconds: float
    is_refusal: bool = False
    groundedness_confidence: float = 1.0

class IngestResponse(BaseModel):
    status: str
    document_path: str
    chunks_created: int
    collection_name: str
    message: str

class EvalTestCaseResult(BaseModel):
    test_id: str
    query: str
    expected_policy_topic: str
    generated_answer: str
    is_refusal_expected: bool
    is_refusal_observed: bool
    faithfulness_score: float
    answer_relevance_score: float
    context_precision_score: float
    grounded: bool
    judge_reasoning: str
    latency_seconds: float

class EvaluationSummary(BaseModel):
    total_tests: int
    avg_faithfulness: float
    avg_relevance: float
    avg_context_precision: float
    groundedness_rate: float
    refusal_accuracy: float
    avg_latency: float
    csv_file: str
    results: List[EvalTestCaseResult]

class HealthStatus(BaseModel):
    status: str
    app_name: str
    version: str
    handbook_present: bool
    handbook_path: str
    vector_store_chunks: int
    embedding_model: str
    llm_model: str
