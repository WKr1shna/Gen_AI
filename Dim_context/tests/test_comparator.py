import pytest
from backend.services.document_service import doc_service

def test_comparator_metrics():
    doc = doc_service.load_sample_document("affidavit")
    comp = doc_service.compare_with_original(doc.id)
    
    assert comp is not None
    assert comp["text_recovery_pct"] >= 95.0
    assert comp["layout_similarity_pct"] >= 95.0
    assert comp["visual_similarity_pct"] >= 85.0
    assert len(comp["pages"]) == 1
    assert "diff_overlay_base64" in comp["pages"][0]
