import pytest
from backend.utils.test_pdf_generator import (
    generate_sample_affidavit_pdf, generate_sample_rental_agreement_pdf, generate_sample_scanned_pdf
)
from backend.pdf_processor.extractor import extract_pdf_data

def test_extract_affidavit_pdf():
    pdf_bytes = generate_sample_affidavit_pdf()
    pages, stats = extract_pdf_data(pdf_bytes)
    
    assert len(pages) == 1
    assert stats.doc_type == "digital"
    assert stats.page_count == 1
    assert stats.total_spans > 15
    assert pages[0].width > 500
    assert pages[0].height > 800
    
    # Check that text content contains key legal phrases
    full_text = " ".join([s.text for s in pages[0].text_spans])
    assert "AFFIDAVIT" in full_text
    assert "RAMESH KUMAR" in full_text
    assert "SUIT NO." in full_text
    assert "_______________________" in full_text  # Check blanks preserved

def test_extract_rental_agreement_multipage():
    pdf_bytes = generate_sample_rental_agreement_pdf()
    pages, stats = extract_pdf_data(pdf_bytes)
    
    assert len(pages) == 2
    assert stats.page_count == 2
    assert stats.total_spans > 25
    
    p1_text = " ".join([s.text for s in pages[0].text_spans])
    assert "RESIDENTIAL LEASE AGREEMENT" in p1_text
    assert "Monthly Rent" in p1_text

def test_extract_scanned_pdf_detection():
    pdf_bytes = generate_sample_scanned_pdf()
    pages, stats = extract_pdf_data(pdf_bytes)
    
    assert len(pages) == 1
    assert pages[0].is_scanned == True
    assert stats.doc_type == "scanned"
