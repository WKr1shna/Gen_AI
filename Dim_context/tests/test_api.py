import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_load_sample_api():
    response = client.post("/api/sample/affidavit")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["doc_type"] == "digital"
    assert len(data["pages"]) == 1
    doc_id = data["id"]
    
    # Check HTML endpoint
    html_resp = client.get(f"/api/document/{doc_id}/html")
    assert html_resp.status_code == 200
    assert "contenteditable" in html_resp.json()["html"]
    
    # Check Compare endpoint
    comp_resp = client.get(f"/api/document/{doc_id}/compare")
    assert comp_resp.status_code == 200
    assert "text_recovery_pct" in comp_resp.json()
    
    # Check Export PDF endpoint
    pdf_resp = client.get(f"/api/document/{doc_id}/export/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    
    # Check Export DOCX endpoint
    docx_resp = client.get(f"/api/document/{doc_id}/export/docx")
    assert docx_resp.status_code == 200
    
    # Check Delete endpoint
    del_resp = client.delete(f"/api/document/{doc_id}")
    assert del_resp.status_code == 200
