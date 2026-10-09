import os
import copy
from typing import Dict, Optional, List, Any, Tuple
from backend.models.document import (
    ReconstructedDocument, DocumentPage, TextElement, FieldElement, DocumentStats,
    UpdateSpanRequest, UpdateFieldRequest, ReplaceTextRequest
)
from backend.pdf_processor.extractor import extract_pdf_data
from backend.pdf_processor.field_detector import detect_fields_in_document
from backend.pdf_processor.reconstruction import (
    generate_editable_html_page, reconstruct_to_pdf_bytes, reconstruct_to_docx_bytes
)
from backend.pdf_processor.comparator import compare_documents
from backend.utils.test_pdf_generator import (
    generate_sample_affidavit_pdf, generate_sample_rental_agreement_pdf, generate_sample_scanned_pdf
)

class DocumentService:
    def __init__(self):
        self._documents: Dict[str, ReconstructedDocument] = {}
        self._original_pdf_bytes: Dict[str, bytes] = {}
        self._history: Dict[str, List[ReconstructedDocument]] = {}
        self._redo_history: Dict[str, List[ReconstructedDocument]] = {}

    def process_file_bytes(self, filename: str, file_bytes: bytes, ignore_pen_ink: bool = True) -> ReconstructedDocument:
        """Processes an uploaded PDF or Image byte stream and converts it to a structured ReconstructedDocument."""
        ext = os.path.splitext(filename)[1].lower().lstrip(".")
        pdf_bytes = file_bytes
        
        # If image, convert to PDF page stream
        if ext in ["png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif"]:
            try:
                import fitz
                img_doc = fitz.open(stream=file_bytes, filetype=ext if ext != "jpg" else "jpeg")
                pdf_bytes = img_doc.convert_to_pdf()
            except Exception as e:
                pass

        pages, stats = extract_pdf_data(pdf_bytes, ignore_pen_ink=ignore_pen_ink)
        pages, global_fields = detect_fields_in_document(pages)
        stats.detected_fields_count = len(global_fields)

        doc = ReconstructedDocument(
            filename=filename,
            filesize_bytes=len(file_bytes),
            doc_type=stats.doc_type,
            pages=pages,
            global_fields=global_fields,
            stats=stats
        )

        self._documents[doc.id] = doc
        self._original_pdf_bytes[doc.id] = pdf_bytes
        self._history[doc.id] = []
        self._redo_history[doc.id] = []
        return doc

    def process_pdf_bytes(self, filename: str, pdf_bytes: bytes, ignore_pen_ink: bool = True) -> ReconstructedDocument:
        return self.process_file_bytes(filename, pdf_bytes, ignore_pen_ink=ignore_pen_ink)

    def load_sample_document(self, sample_type: str = "affidavit") -> ReconstructedDocument:
        """Loads a pre-built legal template for immediate testing."""
        if sample_type == "rental":
            pdf_bytes = generate_sample_rental_agreement_pdf()
            filename = "Residential_Lease_Agreement_Sample.pdf"
        elif sample_type == "scanned":
            pdf_bytes = generate_sample_scanned_pdf()
            filename = "Scanned_Power_Of_Attorney_Sample.pdf"
        else:
            pdf_bytes = generate_sample_affidavit_pdf()
            filename = "Court_Affidavit_Suit_452_2026.pdf"

        return self.process_pdf_bytes(filename, pdf_bytes)

    def get_document(self, doc_id: str) -> Optional[ReconstructedDocument]:
        return self._documents.get(doc_id)

    def _push_history(self, doc_id: str):
        if doc_id in self._documents:
            if doc_id not in self._history:
                self._history[doc_id] = []
            self._history[doc_id].append(self._documents[doc_id].model_copy(deep=True))
            if len(self._history[doc_id]) > 25:
                self._history[doc_id].pop(0)
            self._redo_history[doc_id] = []

    def undo(self, doc_id: str) -> Optional[ReconstructedDocument]:
        if doc_id in self._history and len(self._history[doc_id]) > 0:
            if doc_id not in self._redo_history:
                self._redo_history[doc_id] = []
            self._redo_history[doc_id].append(self._documents[doc_id].model_copy(deep=True))
            prev = self._history[doc_id].pop()
            self._documents[doc_id] = prev
            return prev
        return self.get_document(doc_id)

    def redo(self, doc_id: str) -> Optional[ReconstructedDocument]:
        if doc_id in self._redo_history and len(self._redo_history[doc_id]) > 0:
            if doc_id not in self._history:
                self._history[doc_id] = []
            self._history[doc_id].append(self._documents[doc_id].model_copy(deep=True))
            next_state = self._redo_history[doc_id].pop()
            self._documents[doc_id] = next_state
            return next_state
        return self.get_document(doc_id)

    def update_span_text(self, doc_id: str, req: UpdateSpanRequest) -> Optional[ReconstructedDocument]:
        doc = self.get_document(doc_id)
        if not doc:
            return None

        self._push_history(doc_id)
        for page in doc.pages:
            if page.page_number == req.page_number:
                for span in page.text_spans:
                    if span.id == req.span_id:
                        span.text = req.new_text
                        break
        return doc

    def update_field_value(self, doc_id: str, req: UpdateFieldRequest) -> Optional[ReconstructedDocument]:
        doc = self.get_document(doc_id)
        if not doc:
            return None

        self._push_history(doc_id)
        target_field = None
        for f in doc.global_fields:
            if f.id == req.field_id:
                target_field = f
                f.current_text = req.new_value
                break

        if target_field:
            for page in doc.pages:
                for span in page.text_spans:
                    if span.field_id == target_field.id:
                        span.text = req.new_value
        return doc

    def replace_all_text(self, doc_id: str, req: ReplaceTextRequest) -> Tuple[Optional[ReconstructedDocument], int]:
        doc = self.get_document(doc_id)
        if not doc or not req.find_text:
            return None, 0

        self._push_history(doc_id)
        replaced_count = 0
        
        for page in doc.pages:
            for span in page.text_spans:
                if req.match_case:
                    if req.find_text in span.text:
                        span.text = span.text.replace(req.find_text, req.replace_text)
                        replaced_count += 1
                else:
                    lower_text = span.text.lower()
                    lower_find = req.find_text.lower()
                    if lower_find in lower_text:
                        import re
                        pattern = re.compile(re.escape(req.find_text), re.IGNORECASE)
                        span.text = pattern.sub(req.replace_text, span.text)
                        replaced_count += 1

        for f in doc.global_fields:
            if not req.match_case and req.find_text.lower() in f.current_text.lower():
                import re
                f.current_text = re.compile(re.escape(req.find_text), re.IGNORECASE).sub(req.replace_text, f.current_text)
            elif req.match_case and req.find_text in f.current_text:
                f.current_text = f.current_text.replace(req.find_text, req.replace_text)

        return doc, replaced_count

    def get_page_image_bytes(self, doc_id: str, page_num: int) -> Optional[bytes]:
        orig_bytes = self._original_pdf_bytes.get(doc_id)
        if not orig_bytes:
            return None
        try:
            import fitz
            doc = fitz.open(stream=orig_bytes, filetype="pdf")
            if 1 <= page_num <= len(doc):
                pix = doc[page_num - 1].get_pixmap(dpi=150)
                return pix.tobytes("png")
        except Exception as e:
            print(f"[DocumentService] get_page_image_bytes error: {e}")
        return None

    def get_editable_html(self, doc_id: str) -> Optional[str]:
        doc = self.get_document(doc_id)
        if not doc:
            return None
        html_pages = [generate_editable_html_page(page, idx, len(doc.pages)) for idx, page in enumerate(doc.pages)]
        return "\n".join(html_pages)

    def get_page_editable_html(self, doc_id: str, page_num: int) -> Optional[str]:
        doc = self.get_document(doc_id)
        if not doc or not (1 <= page_num <= len(doc.pages)):
            return None
        return generate_editable_html_page(doc.pages[page_num - 1], page_num - 1, len(doc.pages))

    def export_pdf(self, doc_id: str) -> Optional[bytes]:
        doc = self.get_document(doc_id)
        if not doc:
            return None
        return reconstruct_to_pdf_bytes(doc)

    def export_docx(self, doc_id: str) -> Optional[bytes]:
        doc = self.get_document(doc_id)
        if not doc:
            return None
        return reconstruct_to_docx_bytes(doc)

    def compare_with_original(self, doc_id: str) -> Optional[Dict[str, Any]]:
        doc = self.get_document(doc_id)
        orig_bytes = self._original_pdf_bytes.get(doc_id)
        if not doc or not orig_bytes:
            return None
        return compare_documents(orig_bytes, doc)

    def delete_document(self, doc_id: str) -> bool:
        if doc_id in self._documents:
            del self._documents[doc_id]
        if doc_id in self._original_pdf_bytes:
            del self._original_pdf_bytes[doc_id]
        if doc_id in self._history:
            del self._history[doc_id]
        if doc_id in self._redo_history:
            del self._redo_history[doc_id]
        return True

doc_service = DocumentService()
