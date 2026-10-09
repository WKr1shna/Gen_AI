import fitz
import io
import os
from PIL import Image, ImageFilter, ImageDraw

def generate_sample_affidavit_pdf() -> bytes:
    """
    Generates a realistic legal affidavit PDF with exact court headers,
    underlines, case numbers, party names, and signature blocks.
    """
    doc = fitz.open()
    page = doc.new_page(width=595.28, height=841.89)  # A4
    
    # Border
    page.draw_rect(fitz.Rect(36, 36, 595.28 - 36, 841.89 - 36), color=(0.1, 0.1, 0.1), width=1.2)
    
    # Double inner line for legal header
    page.draw_line(fitz.Point(50, 140), fitz.Point(545, 140), color=(0.2, 0.2, 0.2), width=0.8)
    page.draw_line(fitz.Point(50, 143), fitz.Point(545, 143), color=(0.2, 0.2, 0.2), width=0.8)
    
    # Court Header
    page.insert_text(fitz.Point(130, 75), "IN THE COURT OF THE DISTRICT & SESSIONS JUDGE", fontsize=13, fontname="times-bold")
    page.insert_text(fitz.Point(210, 95), "AT NEW DELHI, INDIA", fontsize=11, fontname="times-bold")
    page.insert_text(fitz.Point(180, 120), "SUIT NO. 452 OF 2026", fontsize=11, fontname="times-bold")
    
    # Parties
    page.insert_text(fitz.Point(50, 170), "IN THE MATTER OF:", fontsize=11, fontname="times-bold")
    page.insert_text(fitz.Point(50, 195), "RAMESH KUMAR", fontsize=11, fontname="times-bold")
    page.insert_text(fitz.Point(50, 210), "S/o Late Sh. Gopal Das, R/o 123 Sample Street, New Delhi", fontsize=10, fontname="times-roman")
    page.insert_text(fitz.Point(430, 200), "... PLAINTIFF", fontsize=11, fontname="times-bold")
    
    page.insert_text(fitz.Point(270, 230), "VERSUS", fontsize=11, fontname="times-bold")
    
    page.insert_text(fitz.Point(50, 260), "SURESH VERMA & ANR.", fontsize=11, fontname="times-bold")
    page.insert_text(fitz.Point(50, 275), "R/o 456 Metro Enclave, New Delhi - 110001", fontsize=10, fontname="times-roman")
    page.insert_text(fitz.Point(415, 265), "... DEFENDANT", fontsize=11, fontname="times-bold")
    
    # Affidavit Title
    page.insert_text(fitz.Point(240, 315), "AFFIDAVIT", fontsize=13, fontname="times-bold")
    
    # Affidavit Body
    clauses = [
        "I, RAMESH KUMAR, aged about 48 years, residing at 123 Sample Street, New Delhi, do hereby solemnly affirm and declare on oath as under:",
        "1. That I am the Plaintiff in the above-captioned suit and well conversant with the facts and circumstances of the case, hence competent to swear this affidavit.",
        "2. That the contents of the accompanying plaint have been drafted under my instructions and the factual contents thereof are true to the best of my knowledge.",
        "3. That the total disputed amount involved herein is Rs. 2,50,000/- (Rupees Two Lakh Fifty Thousand only) payable by the Defendant on or before 15/05/2026.",
        "4. That no part of this claim is false or suppressed from this Hon'ble Court."
    ]
    
    y = 350
    for clause in clauses:
        rect = fitz.Rect(50, y, 545, y + 45)
        page.insert_textbox(rect, clause, fontsize=10.5, fontname="times-roman")
        y += 50
        
    # Verification & Signatures
    page.insert_text(fitz.Point(235, 590), "VERIFICATION", fontsize=11, fontname="times-bold")
    v_text = "Verified at New Delhi on this 12th day of April, 2026, that the contents of paragraphs 1 to 4 are true and correct to my knowledge."
    page.insert_textbox(fitz.Rect(50, 610, 545, 650), v_text, fontsize=10.5, fontname="times-roman")
    
    # Signature Lines
    page.insert_text(fitz.Point(50, 710), "Dated: 12/04/2026", fontsize=10.5, fontname="times-roman")
    page.insert_text(fitz.Point(50, 730), "Place: New Delhi", fontsize=10.5, fontname="times-roman")
    
    page.insert_text(fitz.Point(400, 700), "_______________________", fontsize=10, fontname="courier")
    page.insert_text(fitz.Point(430, 718), "DEPONENT", fontsize=10.5, fontname="times-bold")
    page.insert_text(fitz.Point(380, 740), "(RAMESH KUMAR)", fontsize=10, fontname="times-roman")
    
    # Advocate / Notary Section
    page.insert_text(fitz.Point(50, 780), "Identified by me:", fontsize=9.5, fontname="times-roman")
    page.insert_text(fitz.Point(50, 795), "Advocate (D/1423/2012)", fontsize=9.5, fontname="times-roman")
    
    page.insert_text(fitz.Point(400, 780), "ATTESTED BY NOTARY PUBLIC", fontsize=9, fontname="times-bold")
    page.insert_text(fitz.Point(400, 795), "Govt. of India, Reg. No. 9812", fontsize=8.5, fontname="times-roman")

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def generate_sample_rental_agreement_pdf() -> bytes:
    """
    Generates a 2-page commercial rental agreement with template blanks and tables.
    """
    doc = fitz.open()
    
    # Page 1
    page1 = doc.new_page(width=595.28, height=841.89)
    page1.insert_text(fitz.Point(180, 70), "RESIDENTIAL LEASE AGREEMENT", fontsize=14, fontname="times-bold")
    page1.draw_line(fitz.Point(50, 85), fitz.Point(545, 85), color=(0, 0, 0), width=1.0)
    
    p1_text = (
        "THIS LEASE AGREEMENT is made and entered into on this _____ day of ____________, 2026, "
        "by and between [ LANDLORD NAME ], residing at [ LANDLORD ADDRESS ] (hereinafter referred to as the 'LESSOR'), "
        "AND [ TENANT NAME ], residing at [ TENANT ADDRESS ] (hereinafter referred to as the 'LESSEE').\n\n"
        "WHEREAS the Lessor is the absolute owner of the premises located at: ____________________________________________________.\n\n"
        "AND WHEREAS the Lessee desires to lease the aforementioned premises for residential purposes under the following terms:"
    )
    page1.insert_textbox(fitz.Rect(50, 110, 545, 230), p1_text, fontsize=10.5, fontname="times-roman")
    
    # Terms Table
    page1.draw_rect(fitz.Rect(50, 260, 545, 420), color=(0.2, 0.2, 0.2), width=0.8)
    page1.draw_line(fitz.Point(50, 290), fitz.Point(545, 290), color=(0.2, 0.2, 0.2), width=0.8)
    page1.draw_line(fitz.Point(50, 330), fitz.Point(545, 330), color=(0.2, 0.2, 0.2), width=0.8)
    page1.draw_line(fitz.Point(50, 370), fitz.Point(545, 370), color=(0.2, 0.2, 0.2), width=0.8)
    page1.draw_line(fitz.Point(200, 260), fitz.Point(200, 420), color=(0.2, 0.2, 0.2), width=0.8)
    
    page1.insert_text(fitz.Point(60, 280), "TERMS & PARTICULARS", fontsize=10, fontname="times-bold")
    page1.insert_text(fitz.Point(210, 280), "DETAILS & AMOUNTS", fontsize=10, fontname="times-bold")
    
    page1.insert_text(fitz.Point(60, 315), "Monthly Rent", fontsize=10, fontname="times-roman")
    page1.insert_text(fitz.Point(210, 315), "Rs. 35,000/- (Thirty Five Thousand Rupees)", fontsize=10, fontname="times-bold")
    
    page1.insert_text(fitz.Point(60, 355), "Security Deposit", fontsize=10, fontname="times-roman")
    page1.insert_text(fitz.Point(210, 355), "Rs. 1,00,000/- (Refundable on vacate)", fontsize=10, fontname="times-bold")
    
    page1.insert_text(fitz.Point(60, 400), "Lease Period", fontsize=10, fontname="times-roman")
    page1.insert_text(fitz.Point(210, 400), "11 Months commencing from 01/05/2026", fontsize=10, fontname="times-roman")
    
    # Clauses
    page1.insert_text(fitz.Point(50, 450), "1. PAYMENT OF RENT:", fontsize=10.5, fontname="times-bold")
    page1.insert_textbox(fitz.Rect(50, 465, 545, 510), "The Lessee shall pay the agreed monthly rent in advance on or before the 7th day of each English calendar month through Bank Transfer / Cheque.", fontsize=10, fontname="times-roman")
    
    page1.insert_text(fitz.Point(50, 530), "2. MAINTENANCE & UTILITIES:", fontsize=10.5, fontname="times-bold")
    page1.insert_textbox(fitz.Rect(50, 545, 545, 595), "The Lessee shall bear all electricity, water, and regular society maintenance charges during the subsistence of this agreement.", fontsize=10, fontname="times-roman")
    
    page1.insert_text(fitz.Point(270, 800), "Page 1 of 2", fontsize=9, fontname="times-roman")
    
    # Page 2
    page2 = doc.new_page(width=595.28, height=841.89)
    page2.insert_text(fitz.Point(50, 60), "3. TERMINATION & NOTICE PERIOD:", fontsize=10.5, fontname="times-bold")
    page2.insert_textbox(fitz.Rect(50, 75, 545, 130), "Either party may terminate this agreement by providing one (1) month prior written notice or rent in lieu thereof to the other party.", fontsize=10, fontname="times-roman")
    
    page2.insert_text(fitz.Point(50, 150), "IN WITNESS WHEREOF, the parties hereto have signed this agreement on the date first written above.", fontsize=10.5, fontname="times-roman")
    
    # Signatures
    page2.insert_text(fitz.Point(50, 240), "______________________________", fontsize=10, fontname="courier")
    page2.insert_text(fitz.Point(50, 258), "LESSOR (Landlord)", fontsize=10.5, fontname="times-bold")
    page2.insert_text(fitz.Point(50, 275), "Name: ______________________", fontsize=10, fontname="times-roman")
    
    page2.insert_text(fitz.Point(340, 240), "______________________________", fontsize=10, fontname="courier")
    page2.insert_text(fitz.Point(340, 258), "LESSEE (Tenant)", fontsize=10.5, fontname="times-bold")
    page2.insert_text(fitz.Point(340, 275), "Name: ______________________", fontsize=10, fontname="times-roman")
    
    page2.insert_text(fitz.Point(50, 340), "WITNESS 1:", fontsize=10, fontname="times-bold")
    page2.insert_text(fitz.Point(50, 360), "Signature: ___________________", fontsize=10, fontname="times-roman")
    page2.insert_text(fitz.Point(50, 380), "Name & Address: _____________", fontsize=10, fontname="times-roman")
    
    page2.insert_text(fitz.Point(340, 340), "WITNESS 2:", fontsize=10, fontname="times-bold")
    page2.insert_text(fitz.Point(340, 360), "Signature: ___________________", fontsize=10, fontname="times-roman")
    page2.insert_text(fitz.Point(340, 380), "Name & Address: _____________", fontsize=10, fontname="times-roman")
    
    page2.insert_text(fitz.Point(270, 800), "Page 2 of 2", fontsize=9, fontname="times-roman")
    
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def generate_sample_scanned_pdf() -> bytes:
    """
    Generates a scanned-look legal document by rendering pages as raster images with subtle blur/noise.
    """
    doc = fitz.open()
    page = doc.new_page(width=595.28, height=841.89)
    page.insert_text(fitz.Point(190, 80), "SPECIAL POWER OF ATTORNEY", fontsize=13, fontname="times-bold")
    page.insert_text(fitz.Point(50, 130), "KNOW ALL MEN BY THESE PRESENTS that I, [ PRINCIPAL NAME ],", fontsize=11, fontname="times-roman")
    page.insert_text(fitz.Point(50, 155), "residing at [ PRINCIPAL ADDRESS ], do hereby appoint and constitute:", fontsize=11, fontname="times-roman")
    page.insert_text(fitz.Point(50, 190), "MR. SURESH VERMA, R/o 456 Metro Enclave, New Delhi,", fontsize=11, fontname="times-bold")
    page.insert_text(fitz.Point(50, 220), "as my lawful attorney to act on my behalf before the Hon'ble Court in Suit No. 452/2026.", fontsize=10.5, fontname="times-roman")
    page.insert_text(fitz.Point(50, 270), "Dated: 12/04/2026", fontsize=10.5, fontname="times-roman")
    page.insert_text(fitz.Point(350, 270), "EXECUTANT: ___________________", fontsize=10.5, fontname="times-bold")
    
    pix = page.get_pixmap(dpi=150)
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    img_scanned = img.filter(ImageFilter.GaussianBlur(radius=0.3))
    
    img_stream = io.BytesIO()
    img_scanned.save(img_stream, format="JPEG", quality=85)
    img_stream.seek(0)
    
    scanned_doc = fitz.open()
    s_page = scanned_doc.new_page(width=595.28, height=841.89)
    s_page.insert_image(s_page.rect, stream=img_stream.getvalue())
    
    pdf_bytes = scanned_doc.tobytes()
    doc.close()
    scanned_doc.close()
    return pdf_bytes
