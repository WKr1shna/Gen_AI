"""
FastAPI Test Suite for MirAI Student Policy Advisor endpoints.
"""
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "MirAI Student Policy Advisor" in data["message"]

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["handbook_present"] is True
    assert data["vector_store_chunks"] > 0
    assert "gemini" in data["embedding_model"].lower()

def test_query_endpoint():
    payload = {
        "question": "What is the CGPA needed to maintain the MirAI Merit Scholarship?",
        "top_k": 3
    }
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "8.5" in data["answer"]
    assert len(data["sources"]) > 0
    assert data["is_refusal"] is False

def test_query_refusal_endpoint():
    payload = {
        "question": "What is the price of ice cream at the campus cafeteria?",
        "top_k": 3
    }
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_refusal"] is True

if __name__ == "__main__":
    test_root_endpoint()
    print("test_root_endpoint passed.")
    test_health_endpoint()
    print("test_health_endpoint passed.")
    test_query_endpoint()
    print("test_query_endpoint passed.")
    test_query_refusal_endpoint()
    print("test_query_refusal_endpoint passed.")
