import pytest
import io
import fitz
from PIL import Image, ImageChops, ImageStat
from backend.services.document_service import doc_service
from backend.models.document import UpdateSpanRequest

def generate_complex_fidelity_test_pdf() -> bytes:
    """
    Creates a comprehensive legal test document containing all complex legal formatting:
    - Centered headings
    - Left-aligned paragraphs
    - Right-aligned text
    - Blank lines
    - Underscores
    - Single and double horizontal rules
    - Different font sizes and bold text
    - Multi-line paragraphs
    - Signature area
    - Table
    - Page footer
    """
    doc = fitz.open()
    page = doc.new_page(width=595.28, height=841.89)
    
    # Outer legal border
    page.draw_rect(fitz.Rect(30, 30, 565.28, 811.89), color=(0.1, 0.1, 0.1), width=1.0)
    
    # Double horizontal rule under title
    page.draw_line(fitz.Point(50, 110), fitz.Point(545, 110), color=(0.2, 0.2, 0.2), width=0.8)
    page.draw_line(fitz.Point(50, 113), fitz.Point(545, 113), color=(0.2, 0.2, 0.2), width=0.8)
    
    # Table border and lines
    page.draw_rect(fitz.Rect(50, 380, 545, 480), color=(0.3, 0.3, 0.3), width=0.8)
    page.draw_line(fitz.Point(50, 410), fitz.Point(545, 410), color=(0.3, 0.3, 0.3), width=0.8)
    page.draw_line(fitz.Point(200, 380), fitz.Point(200, 480), color=(0.3, 0.3, 0.3), width=0.8)
    page.draw_line(fitz.Point(370, 380), fitz.Point(370, 480), color=(0.3, 0.3, 0.3), width=0.8)
    
    # 1. Centered heading
    page.insert_text(fitz.Point(160, 70), "IN THE HIGH COURT OF JUDICATURE", fontsize=14, fontname="times-bold")
    page.insert_text(fitz.Point(210, 92), "CIVIL APPELLATE JURISDICTION", fontsize=11, fontname="times-bold")
    
    # 2. Right-aligned text
    page.insert_text(fitz.Point(410, 140), "CASE NO: W.P. 9021/2026", fontsize=10, fontname="times-bold")
    
    # 3. Left-aligned legal title
    page.insert_text(fitz.Point(50, 170), "MEMORANDUM OF SETTLEMENT", fontsize=12, fontname="times-bold")
    
    # 4. Multi-line paragraph with blank lines & underscores
    para1 = (
        "THIS SETTLEMENT AGREEMENT is entered into on this 12th day of April, 2026, by and between "
        "MR. ANAND VERMA, residing at 456 Metro Enclave, New Delhi (Party of the First Part), "
        "AND MS. PRIYA SHARMA, residing at 789 Park View, New Delhi (Party of the Second Part)."
    )
    page.insert_textbox(fitz.Rect(50, 190, 545, 245), para1, fontsize=10.5, fontname="times-roman")
    
    page.insert_text(fitz.Point(50, 265), "WHEREAS the parties have mutually agreed upon the following terms:", fontsize=10.5, fontname="times-bold")
    
    page.insert_textbox(fitz.Rect(50, 285, 545, 335), 
        "1. That the First Party shall pay an agreed sum of Rs. 5,00,000/- (Rupees Five Lakhs only) "
        "to the Second Party on or before 30/05/2026 towards full and final settlement of all claims.",
        fontsize=10.5, fontname="times-roman")
    
    page.insert_textbox(fitz.Rect(50, 340, 545, 375), 
        "2. That both parties undertake not to institute any further proceedings in relation to the subject property.",
        fontsize=10.5, fontname="times-roman")
    
    # 5. Table contents
    page.insert_text(fitz.Point(60, 400), "SCHEDULE", fontsize=10, fontname="times-bold")
    page.insert_text(fitz.Point(210, 400), "PARTICULARS", fontsize=10, fontname="times-bold")
    page.insert_text(fitz.Point(380, 400), "SETTLEMENT AMOUNT", fontsize=10, fontname="times-bold")
    
    page.insert_text(fitz.Point(60, 440), "Installment 1", fontsize=10, fontname="times-roman")
    page.insert_text(fitz.Point(210, 440), "Initial Escrow Deposit", fontsize=10, fontname="times-roman")
    page.insert_text(fitz.Point(380, 440), "Rs. 2,50,000/-", fontsize=10, fontname="times-bold")
    
    page.insert_text(fitz.Point(60, 470), "Installment 2", fontsize=10, fontname="times-roman")
    page.insert_text(fitz.Point(210, 470), "Final Closing Transfer", fontsize=10, fontname="times-roman")
    page.insert_text(fitz.Point(380, 470), "Rs. 2,50,000/-", fontsize=10, fontname="times-bold")
    
    # 6. Signature area with explicit underscores
    page.insert_text(fitz.Point(50, 560), "IN WITNESS WHEREOF the parties have affixed their signatures below:", fontsize=10.5, fontname="times-roman")
    
    page.insert_text(fitz.Point(50, 640), "______________________________", fontsize=10, fontname="courier")
    page.insert_text(fitz.Point(50, 658), "FIRST PARTY (ANAND VERMA)", fontsize=10.5, fontname="times-bold")
    page.insert_text(fitz.Point(50, 675), "Date: 12/04/2026", fontsize=10, fontname="times-roman")
    
    page.insert_text(fitz.Point(340, 640), "______________________________", fontsize=10, fontname="courier")
    page.insert_text(fitz.Point(340, 658), "SECOND PARTY (PRIYA SHARMA)", fontsize=10.5, fontname="times-bold")
    page.insert_text(fitz.Point(340, 675), "Date: 12/04/2026", fontsize=10, fontname="times-roman")
    
    # 7. Page footer
    page.insert_text(fitz.Point(255, 790), "Page 1 of 1 - High Court Certified", fontsize=9, fontname="times-roman")
    
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def test_complex_fidelity_reconstruction_and_overlay():
    pdf_bytes = generate_complex_fidelity_test_pdf()
    doc = doc_service.process_pdf_bytes("Complex_Fidelity_Test.pdf", pdf_bytes)
    
    assert doc is not None
    assert len(doc.pages) == 1
    assert doc.stats.total_spans > 20
    assert doc.stats.total_lines >= 5
    
    # Compare original and reconstructed
    comp = doc_service.compare_with_original(doc.id)
    assert comp is not None
    
    assert comp["text_recovery_pct"] == 100.0
    assert comp["layout_similarity_pct"] >= 98.0
    assert comp["visual_similarity_pct"] >= 90.0
    assert comp["major_mismatches"] == 0

def test_field_editing_without_geometry_shift():
    pdf_bytes = generate_complex_fidelity_test_pdf()
    doc = doc_service.process_pdf_bytes("Complex_Fidelity_Test_Edit.pdf", pdf_bytes)
    
    # Find span for "ANAND VERMA" and edit it to "RAHUL AGGARWAL"
    target_span = None
    for span in doc.pages[0].text_spans:
        if "ANAND VERMA" in span.text:
            target_span = span
            break
            
    assert target_span is not None
    orig_x = target_span.x
    orig_y = target_span.y
    
    updated_doc = doc_service.update_span_text(doc.id, UpdateSpanRequest(
        span_id=target_span.id,
        new_text="FIRST PARTY (RAHUL AGGARWAL)",
        page_number=1
    ))
    
    edited_span = [s for s in updated_doc.pages[0].text_spans if s.id == target_span.id][0]
    assert edited_span.x == orig_x
    assert edited_span.y == orig_y
    assert edited_span.text == "FIRST PARTY (RAHUL AGGARWAL)"
