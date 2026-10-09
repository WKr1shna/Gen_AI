"""
Automated Test Suite for MirAI Strict RAG Pipeline.
"""
import pytest
from app.config import settings
from app.ingestion import ingest_handbook, get_db_stats
from app.rag_engine import query_policy_handbook, STRICT_REFUSAL_PHRASE

def test_ingestion_and_db_ready():
    """Verify that handbook ingestion succeeds and stores chunks in ChromaDB."""
    stats = get_db_stats()
    if stats.get("indexed_chunks", 0) == 0:
        res = ingest_handbook(force_reingest=False)
        assert res["status"] in ["success", "already_indexed"]
    
    current_stats = get_db_stats()
    assert current_stats.get("indexed_chunks", 0) > 0

def test_attendance_policy_grounded_answer():
    """Verify grounded answer and citation for attendance policy."""
    query = "What is the mandatory minimum attendance percentage required in registered courses?"
    res = query_policy_handbook(query, use_multi_query=False)
    
    assert res.is_refusal is False
    assert ("85%" in res.answer or "85 percent" in res.answer.lower())
    assert len(res.sources) > 0
    assert any("Mirai_SoT_Policy_Handbook" in s.source for s in res.sources)

def test_academic_credits_policy():
    """Verify minimum and maximum credit requirements."""
    query = "What is the minimum and maximum credit load allowed per semester?"
    res = query_policy_handbook(query, use_multi_query=False)
    
    assert res.is_refusal is False
    assert "20" in res.answer
    assert "26" in res.answer

def test_strict_refusal_on_out_of_scope_query():
    """Verify deterministic refusal on queries not covered by handbook."""
    query = "How do I book a private submarine tour at the college lake?"
    res = query_policy_handbook(query, use_multi_query=False)
    
    assert res.is_refusal is True
    assert (
        STRICT_REFUSAL_PHRASE.lower() in res.answer.lower() or
        "cannot answer this based on the official" in res.answer.lower() or
        "not specified in the document" in res.answer.lower()
    )

if __name__ == "__main__":
    test_ingestion_and_db_ready()
    print("test_ingestion_and_db_ready passed.")
    test_attendance_policy_grounded_answer()
    print("test_attendance_policy_grounded_answer passed.")
    test_academic_credits_policy()
    print("test_academic_credits_policy passed.")
    test_strict_refusal_on_out_of_scope_query()
    print("test_strict_refusal_on_out_of_scope_query passed.")
