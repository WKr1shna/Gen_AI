import pytest
from backend.utils.test_pdf_generator import generate_sample_affidavit_pdf, generate_sample_rental_agreement_pdf
from backend.pdf_processor.extractor import extract_pdf_data
from backend.pdf_processor.field_detector import detect_fields_in_document

def test_detect_fields_in_affidavit():
    pdf_bytes = generate_sample_affidavit_pdf()
    pages, stats = extract_pdf_data(pdf_bytes)
    pages, global_fields = detect_fields_in_document(pages)
    
    assert len(global_fields) > 0
    field_labels = [f.label for f in global_fields]
    assert any("CASE" in l or "DATE" in l or "PLACE" in l or "BLANK" in l or "PARTY" in l for l in field_labels)

def test_detect_template_vars_in_rental():
    pdf_bytes = generate_sample_rental_agreement_pdf()
    pages, stats = extract_pdf_data(pdf_bytes)
    pages, global_fields = detect_fields_in_document(pages)
    
    assert len(global_fields) > 0
    all_texts = [f.original_text for f in global_fields]
    assert any("LANDLORD" in t or "TENANT" in t or "____" in t for t in all_texts)
