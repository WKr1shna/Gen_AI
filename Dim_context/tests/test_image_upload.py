import io
from PIL import Image, ImageDraw, ImageFont
from backend.services.document_service import doc_service
from context import load_documents

def create_sample_legal_image_bytes() -> bytes:
    """Creates a sample legal receipt / certificate image for testing."""
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Border
    draw.rectangle([20, 20, 580, 780], outline=(0, 0, 0), width=2)
    
    # Text lines
    draw.text((150, 60), "LEGAL NOTICE & RECEIPT", fill=(0, 0, 0))
    draw.text((50, 120), "CASE NO: REC-8821/2026", fill=(0, 0, 0))
    draw.text((50, 160), "DATE: 12/04/2026", fill=(0, 0, 0))
    draw.text((50, 200), "AMOUNT: Rs. 50,000/-", fill=(0, 0, 0))
    draw.text((50, 260), "RECEIVED FROM: MR. RAMESH KUMAR", fill=(0, 0, 0))
    draw.text((50, 320), "SIGNATURE: _______________________", fill=(0, 0, 0))
    
    stream = io.BytesIO()
    img.save(stream, format="PNG")
    return stream.getvalue()

def test_document_service_image_processing():
    img_bytes = create_sample_legal_image_bytes()
    doc = doc_service.process_file_bytes("legal_receipt.png", img_bytes)
    
    assert doc is not None
    assert len(doc.pages) == 1
    assert doc.doc_type in ["scanned", "digital", "mixed"]
    assert doc.pages[0].width > 0
    assert doc.pages[0].height > 0
    assert len(doc.pages[0].text_spans) > 0, "OCR should extract text spans from the legal image"
    
    # Verify DOCX export is non-empty and has actual document content
    docx_bytes = doc_service.export_docx(doc.id)
    assert docx_bytes is not None
    assert len(docx_bytes) > 2000, "Exported DOCX should be a full Word document"
    
    # Verify PDF export
    pdf_bytes = doc_service.export_pdf(doc.id)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 1000, "Exported PDF should be non-empty"

def test_context_image_loading():
    img_bytes = create_sample_legal_image_bytes()
    test_img_path = "test_receipt.png"
    with open(test_img_path, "wb") as f:
        f.write(img_bytes)
        
    try:
        docs = load_documents(test_img_path)
        assert len(docs) > 0
        assert docs[0].metadata["type"] == "image"
    finally:
        import os
        if os.path.exists(test_img_path):
            os.remove(test_img_path)
