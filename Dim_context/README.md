# LexiRecon: High-Fidelity Legal Document Reconstructor & Editor

**LexiRecon** is a local-first, coordinate-accurate document conversion application designed specifically for real-world legal workflows.

Many legal documents (affidavits, court petitions, lease agreements, powers of attorney, deeds) contain exact visual positioning, template blanks (`Name: _________________`), court headers, tables, double rules, and signature blocks where only a few variables change from case to case.

LexiRecon preserves the exact visual layout and coordinate positioning of the original PDF while giving the lawyer a rich, in-place editable document that can be exported back to **print-ready vector PDF** or **editable Microsoft Word (DOCX)**.

---

## 🌟 Key Features

1. **Pixel-Perfect Coordinate Reconstruction**:
   - Extracts bounding boxes (`x, y, width, height`), baseline origins, font family, font size, bold/italic styles, and hex colors directly from PDF streams.
   - Preserves whitespace, multiple spaces, underscores `_______`, and dashes without destructive normalization.
   - Extracts vector drawings (lines, borders, double rules) and embedded images (seals, stamps, signatures).

2. **Smart Legal Field & Placeholder Detection**:
   - Automatically identifies fillable blanks (`Name: _______`, `Date: _______`, `Signature: _______`).
   - Identifies court headers (`BEFORE THE HON'BLE COURT OF _______`, `WHEREAS _______`).
   - Extracts key variables: Party Names, Case Numbers, Dates, Monetary Amounts, and bracketed tokens (`[ LANDLORD NAME ]`, `{{CASE_NO}}`).
   - Dedicated **Smart Form Inspector** lets the user type new values and updates all occurrences across the document in real time.

3. **Multi-Type PDF Support**:
   - **Digitally Generated PDFs**: Exact vector and font metric extraction.
   - **Scanned PDFs**: OCR bounding-box recognition with coordinate alignment.
   - **Mixed PDFs**: Selectable text extraction on digital pages, OCR on scanned pages.

4. **Side-by-Side & Visual Diff Comparison**:
   - Side-by-side synchronized scrolling between the original PDF and the editable reconstructed version.
   - **Overlay Diff Mode**: Interactive opacity slider to verify 1:1 visual alignment.
   - Live similarity metrics: Page count ratio, Text Recovery %, Layout Similarity %, and Visual Similarity %.

5. **Multi-Format Export**:
   - **Export PDF**: Generates print-ready vector PDF rendering your edits at exact coordinates with the original lines and images.
   - **Export DOCX**: Generates structured Word documents with paragraph alignments, runs, and table layouts.
   - **Direct Print**: Print directly to office printers.

6. **Local Privacy Compliance**:
   - Operates 100% locally on your machine.
   - No sensitive legal client data is sent to external APIs.
   - One-click **Delete Document** button to securely wipe loaded documents from memory.

---

## 📁 Project Structure

```
├── backend/
│   ├── main.py                   # FastAPI application & REST endpoints
│   ├── models/
│   │   └── document.py           # Pydantic models for Document, Page, TextSpan, Lines, Fields
│   ├── pdf_processor/
│   │   ├── extractor.py          # Coordinate extraction (text, fonts, lines, drawings, tables)
│   │   ├── ocr.py                # OCR engine for scanned pages
│   │   ├── field_detector.py     # Smart template variable & blank detector
│   │   ├── reconstruction.py     # Interactive HTML, vector PDF & DOCX generators
│   │   └── comparator.py         # Visual difference, text similarity & overlay metrics
│   ├── services/
│   │   └── document_service.py   # State management, undo/redo, and export lifecycle
│   └── utils/
│       └── test_pdf_generator.py # Sample legal document generators
├── frontend/
│   ├── index.html                # 3-column workstation interface
│   ├── css/style.css             # Polished dark/light legal workstation theme
│   └── js/app.js                 # Interactive client logic, live edits, sync scroll, diff overlay
├── tests/
│   ├── test_extractor.py         # Extraction & type detection tests
│   ├── test_field_detector.py    # Smart field detection tests
│   ├── test_reconstruction.py    # Reconstruct, edit, undo/redo, PDF & DOCX export tests
│   ├── test_comparator.py        # Similarity & visual diff tests
│   └── test_api.py               # REST API endpoint tests
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
```
Open your browser and navigate to:
```
http://localhost:8080
```

### 3. Run Automated Tests
```bash
PYTHONPATH=. pytest tests/
```
