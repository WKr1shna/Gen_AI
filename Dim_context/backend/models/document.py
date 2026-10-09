from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid

class BaseElement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    page: int = 1
    type: str = "text"  # text, line, rect, image, table, field
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    z_index: int = 1

class TextElement(BaseElement):
    type: str = "text"
    text: str
    original_text: str = ""
    font_family: str = "Times New Roman"
    font_size: float = 11.0
    font_weight: str = "normal"  # normal, bold
    font_style: str = "normal"  # normal, italic
    color: str = "#000000"
    origin_y: Optional[float] = None
    is_field: bool = False
    field_id: Optional[str] = None
    field_type: Optional[str] = None
    block_index: Optional[int] = 0
    line_index: Optional[int] = 0
    span_index: Optional[int] = 0

TextSpan = TextElement

class LineElement(BaseElement):
    type: str = "line"
    x1: float
    y1: float
    x2: float
    y2: float
    line_width: float = 1.0
    color: str = "#000000"
    style: str = "solid"

class RectElement(BaseElement):
    type: str = "rect"
    stroke_color: Optional[str] = None
    fill_color: Optional[str] = None
    line_width: float = 1.0

class ImageElement(BaseElement):
    type: str = "image"
    image_base64: str = ""
    mime_type: str = "image/png"
    name: Optional[str] = "image"

class TableCell(BaseModel):
    row: int
    col: int
    text: str
    bbox: List[float]

class TableElement(BaseElement):
    type: str = "table"
    bbox: List[float]
    rows: int
    cols: int
    cells: List[TableCell] = []

class FieldElement(BaseElement):
    type: str = "field"
    field_type: str
    label: str
    original_text: str
    current_text: str
    confidence: float = 0.95
    editable: bool = True
    span_ids: List[str] = []
    occurrence_count: int = 1

    @property
    def original_value(self) -> str:
        return self.original_text

    @property
    def current_value(self) -> str:
        return self.current_text

SmartField = FieldElement

class DocumentStats(BaseModel):
    page_count: int = 1
    total_elements: int = 0
    total_spans: int = 0
    total_lines: int = 0
    total_images: int = 0
    total_tables: int = 0
    detected_fields_count: int = 0
    doc_type: str = "digital"  # digital, scanned, mixed
    text_recovery_pct: float = 100.0
    layout_similarity_pct: float = 98.5
    visual_similarity_pct: float = 97.0
    elements_compared: int = 0
    major_mismatches: int = 0

class DocumentPage(BaseModel):
    page_number: int
    width: float = 595.28  # A4 width in pt
    height: float = 841.89  # A4 height in pt
    is_scanned: bool = False
    original_image_base64: Optional[str] = None
    text_spans: List[TextElement] = []
    lines: List[LineElement] = []
    rects: List[RectElement] = []
    images: List[ImageElement] = []
    tables: List[TableElement] = []
    fields: List[FieldElement] = []

class ReconstructedDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    filesize_bytes: int = 0
    doc_type: str = "digital"
    pages: List[DocumentPage] = []
    global_fields: List[FieldElement] = []
    stats: DocumentStats = Field(default_factory=DocumentStats)

class UpdateSpanRequest(BaseModel):
    span_id: str
    new_text: str
    page_number: int

class UpdateFieldRequest(BaseModel):
    field_id: str
    new_value: str
    apply_to_all_occurrences: bool = True

class ReplaceTextRequest(BaseModel):
    find_text: str
    replace_text: str
    match_case: bool = False
    whole_word: bool = False
