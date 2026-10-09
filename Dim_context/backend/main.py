import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from typing import Optional

from backend.models.document import (
    ReconstructedDocument, UpdateSpanRequest, UpdateFieldRequest, ReplaceTextRequest
)
from backend.services.document_service import doc_service

app = FastAPI(
    title="LexiRecon - High-Fidelity Legal Document Reconstructor",
    description="Local-first PDF to Editable Document Engine preserving pixel-accurate legal layouts",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response

from starlette.concurrency import run_in_threadpool

SUPPORTED_UPLOAD_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}

@app.post("/api/upload", response_model=ReconstructedDocument)
async def upload_document(
    file: UploadFile = File(...),
    ignore_pen_ink: bool = Form(default=True)
):
    """Uploads a PDF or Image and reconstructs it with exact coordinates, fonts, and smart fields."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_UPLOAD_EXTS:
        raise HTTPException(status_code=400, detail="Supported file formats: PDF, PNG, JPG, JPEG, WEBP, TIFF, BMP.")
    
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        
    doc = await run_in_threadpool(doc_service.process_file_bytes, file.filename, contents, ignore_pen_ink)
    return doc

@app.post("/api/sample/{sample_type}", response_model=ReconstructedDocument)
async def load_sample(sample_type: str = "affidavit"):
    """Loads a realistic pre-built legal document (affidavit, rental, scanned)."""
    return await run_in_threadpool(doc_service.load_sample_document, sample_type)

@app.get("/api/document/{doc_id}", response_model=ReconstructedDocument)
async def get_document(doc_id: str):
    doc = doc_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc

@app.get("/api/document/{doc_id}/html")
async def get_document_html(doc_id: str):
    html = doc_service.get_editable_html(doc_id)
    if html is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"html": html}

@app.get("/api/document/{doc_id}/page/{page_num}/html")
async def get_page_html(doc_id: str, page_num: int):
    html = doc_service.get_page_editable_html(doc_id, page_num)
    if html is None:
        raise HTTPException(status_code=404, detail="Page not found.")
    return {"html": html}

@app.get("/api/document/{doc_id}/page/{page_num}/image")
async def get_page_image(doc_id: str, page_num: int):
    img_bytes = await run_in_threadpool(doc_service.get_page_image_bytes, doc_id, page_num)
    if not img_bytes:
        raise HTTPException(status_code=404, detail="Page image not found.")
    return Response(
        content=img_bytes,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"}
    )

@app.post("/api/document/{doc_id}/update-span", response_model=ReconstructedDocument)
async def update_span(doc_id: str, req: UpdateSpanRequest):
    doc = doc_service.update_span_text(doc_id, req)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc

@app.post("/api/document/{doc_id}/update-field", response_model=ReconstructedDocument)
async def update_field(doc_id: str, req: UpdateFieldRequest):
    doc = doc_service.update_field_value(doc_id, req)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc

@app.post("/api/document/{doc_id}/replace-text")
async def replace_text(doc_id: str, req: ReplaceTextRequest):
    doc, count = doc_service.replace_all_text(doc_id, req)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"document": doc, "replaced_count": count}

@app.post("/api/document/{doc_id}/undo", response_model=ReconstructedDocument)
async def undo_edit(doc_id: str):
    doc = doc_service.undo(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc

@app.post("/api/document/{doc_id}/redo", response_model=ReconstructedDocument)
async def redo_edit(doc_id: str):
    doc = doc_service.redo(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc

@app.get("/api/document/{doc_id}/compare")
async def compare_doc(doc_id: str):
    diff_data = doc_service.compare_with_original(doc_id)
    if not diff_data:
        raise HTTPException(status_code=404, detail="Document not found or cannot be compared.")
    return diff_data

@app.get("/api/document/{doc_id}/export/pdf")
async def export_pdf(doc_id: str):
    pdf_bytes = await run_in_threadpool(doc_service.export_pdf, doc_id)
    if not pdf_bytes:
        raise HTTPException(status_code=404, detail="Document not found.")
    doc = doc_service.get_document(doc_id)
    filename = f"edited_{doc.filename}" if doc else "reconstructed_document.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.get("/api/document/{doc_id}/export/docx")
async def export_docx(doc_id: str):
    docx_bytes = await run_in_threadpool(doc_service.export_docx, doc_id)
    if not docx_bytes:
        raise HTTPException(status_code=404, detail="Document not found.")
    doc = doc_service.get_document(doc_id)
    base_name = os.path.splitext(doc.filename)[0] if doc else "document"
    filename = f"{base_name}_editable.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.delete("/api/document/{doc_id}")
async def delete_document(doc_id: str):
    doc_service.delete_document(doc_id)
    return {"status": "deleted", "message": "Document permanently removed from local memory."}

# Mount frontend directory
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
async def root():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>LexiRecon Backend is Running.</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
