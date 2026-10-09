import pytest
import io
import fitz
from docx import Document
from backend.services.document_service import doc_service
from backend.models.document import UpdateSpanRequest, UpdateFieldRequest, ReplaceTextRequest

def test_full_reconstruction_pipeline():
    doc = doc_service.load_sample_document("affidavit")
    assert doc is not None
    assert len(doc.pages) == 1
    
    # 1. Test HTML generation
    html = doc_service.get_editable_html(doc.id)
    assert html is not None
    assert "contenteditable" in html
    assert "AFFIDAVIT" in html
    
    # 2. Test Span editing
    first_span = doc.pages[0].text_spans[0]
    original_text = first_span.text
    updated = doc_service.update_span_text(doc.id, UpdateSpanRequest(
        span_id=first_span.id,
        new_text="IN THE HIGH COURT OF DELHI",
        page_number=1
    ))
    assert updated.pages[0].text_spans[0].text == "IN THE HIGH COURT OF DELHI"
    
    # 3. Test Undo
    undone = doc_service.undo(doc.id)
    assert undone.pages[0].text_spans[0].text == original_text
    
    # 4. Test Redo
    redone = doc_service.redo(doc.id)
    assert redone.pages[0].text_spans[0].text == "IN THE HIGH COURT OF DELHI"
    
    # 5. Test Export to PDF
    pdf_bytes = doc_service.export_pdf(doc.id)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 500
    pdf_check = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert len(pdf_check) == 1
    pdf_text = pdf_check[0].get_text()
    assert "IN THE HIGH COURT OF DELHI" in pdf_text
    
    # 6. Test Export to DOCX
    docx_bytes = doc_service.export_docx(doc.id)
    assert docx_bytes is not None
    assert len(docx_bytes) > 1000
    docx_check = Document(io.BytesIO(docx_bytes))
    docx_full_text = " ".join([p.text for p in docx_check.paragraphs])
    assert "IN THE HIGH COURT OF DELHI" in docx_full_text
