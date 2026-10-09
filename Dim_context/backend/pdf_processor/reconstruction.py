import io
import os
import re
import base64
import fitz
from typing import List, Optional
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from backend.models.document import ReconstructedDocument, DocumentPage, TextElement, LineElement, RectElement, ImageElement

def hex_to_rgb_tuple(hex_str: Optional[str]) -> Optional[tuple]:
    """Converts hex color string to normalized (r, g, b) float tuple."""
    if not hex_str or not hex_str.startswith("#") or len(hex_str) < 7:
        return None
    try:
        r = int(hex_str[1:3], 16) / 255.0
        g = int(hex_str[3:5], 16) / 255.0
        b = int(hex_str[5:7], 16) / 255.0
        return (r, g, b)
    except Exception:
        return (0.0, 0.0, 0.0)

def hex_to_docx_rgb(hex_str: Optional[str]) -> RGBColor:
    """Converts hex string to docx RGBColor."""
    if not hex_str or not hex_str.startswith("#") or len(hex_str) < 7:
        return RGBColor(0, 0, 0)
    try:
        return RGBColor(int(hex_str[1:3], 16), int(hex_str[3:5], 16), int(hex_str[5:7], 16))
    except Exception:
        return RGBColor(0, 0, 0)

def generate_editable_html_page(page: DocumentPage, page_index: int, total_pages: int) -> str:
    """
    Generates a fixed-coordinate, pixel-accurate HTML representation of a single PDF page.
    Uses absolute positioning on every span with exact point coordinates, fonts, and SVG vector drawings.
    """
    html_parts = []
    
    # 1. Page container strictly matching PDF page dimensions in points
    html_parts.append(
        f'<div class="doc-page" id="page-{page.page_number}" '
        f'data-page="{page.page_number}" data-base-width="{page.width}" data-base-height="{page.height}" '
        f'style="width: {page.width}pt; height: {page.height}pt; position: relative; background: #ffffff; '
        f'margin: 0 auto 30px auto; box-shadow: 0 4px 20px rgba(0,0,0,0.25); border-radius: 2px; overflow: hidden; box-sizing: border-box;">'
    )
    
    # 2. Vector Drawings (Lines & Rectangles) rendered via SVG with explicit viewBox
    svg_elements = []
    for line in page.lines:
        svg_elements.append(
            f'<line x1="{line.x1}" y1="{line.y1}" x2="{line.x2}" y2="{line.y2}" '
            f'stroke="{line.color}" stroke-width="{line.line_width}" />'
        )
    for rect in page.rects:
        stroke = f'stroke="{rect.stroke_color}" stroke-width="{rect.line_width}"' if rect.stroke_color else 'stroke="none"'
        fill = f'fill="{rect.fill_color}"' if rect.fill_color else 'fill="none"'
        svg_elements.append(
            f'<rect x="{rect.x}" y="{rect.y}" width="{rect.width}" height="{rect.height}" {stroke} {fill} />'
        )
        
    if svg_elements:
        html_parts.append(
            f'<svg class="page-drawings" viewBox="0 0 {page.width} {page.height}" width="{page.width}pt" height="{page.height}pt" '
            f'style="position: absolute; left: 0; top: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1;">'
            f'{"".join(svg_elements)}'
            f'</svg>'
        )
        
    # 3. Embedded Images (Seals, Stamps, Logos, Signatures)
    for img in page.images:
        if img.image_base64:
            html_parts.append(
                f'<img class="doc-image" src="data:{img.mime_type};base64,{img.image_base64}" '
                f'style="position: absolute; left: {img.x}pt; top: {img.y}pt; width: {img.width}pt; height: {img.height}pt; z-index: 2; pointer-events: none;" />'
            )
            
    # 4. Text Spans with Absolute PDF Coordinates and In-Place Contenteditable
    for span in page.text_spans:
        font_weight = "bold" if span.font_weight == "bold" else "normal"
        font_style = "italic" if span.font_style == "italic" else "normal"
        field_class = "smart-field-highlight" if span.is_field else ""
        field_attr = f'data-field-id="{span.field_id}" data-field-type="{span.field_type}"' if span.is_field else ""
        
        escaped_text = (
            span.text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        
        font_family = f"'{span.font_family}', 'Times New Roman', serif"
        if "courier" in span.font_family.lower():
            font_family = "'Courier New', monospace"
        elif "arial" in span.font_family.lower() or "helvetica" in span.font_family.lower():
            font_family = "'Arial', 'Helvetica', sans-serif"

        html_parts.append(
            f'<span class="text-span {field_class}" id="span-{span.id}" '
            f'data-span-id="{span.id}" data-page="{page.page_number}" {field_attr} '
            f'contenteditable="true" spellcheck="false" '
            f'style="position: absolute; left: {span.x}pt; top: {span.y}pt; '
            f'font-family: {font_family}; font-size: {span.font_size}pt; '
            f'font-weight: {font_weight}; font-style: {font_style}; color: {span.color}; '
            f'white-space: pre; line-height: 1.0; margin: 0; padding: 0; z-index: 5; cursor: text; outline: none;">'
            f'{escaped_text}'
            f'</span>'
        )
        
    html_parts.append('</div>')
    return "\n".join(html_parts)

def reconstruct_to_pdf_bytes(reconstructed_doc: ReconstructedDocument) -> bytes:
    """
    Compiles the edited document elements back into a print-ready vector PDF byte stream.
    Renders text at exact point coordinates using PyMuPDF with matching fonts, sizes, vector drawings and images.
    """
    pdf_out = fitz.open()
    
    for page_data in reconstructed_doc.pages:
        page = pdf_out.new_page(width=page_data.width, height=page_data.height)
        
        # 1. Vector Drawings (Lines & Rectangles)
        for line in page_data.lines:
            rgb = hex_to_rgb_tuple(line.color) or (0.0, 0.0, 0.0)
            page.draw_line(fitz.Point(line.x1, line.y1), fitz.Point(line.x2, line.y2), color=rgb, width=line.line_width)
            
        for rect in page_data.rects:
            stroke_rgb = hex_to_rgb_tuple(rect.stroke_color)
            fill_rgb = hex_to_rgb_tuple(rect.fill_color)
            page.draw_rect(
                fitz.Rect(rect.x, rect.y, rect.x + rect.width, rect.y + rect.height),
                color=stroke_rgb,
                fill=fill_rgb,
                width=rect.line_width
            )
            
        # 2. Images (Stamps, Signatures, Seals)
        for img in page_data.images:
            if img.image_base64:
                try:
                    img_bytes = base64.b64decode(img.image_base64)
                    rect = fitz.Rect(img.x, img.y, img.x + img.width, img.y + img.height)
                    page.insert_image(rect, stream=img_bytes)
                except Exception:
                    pass
                    
        # 3. Text Elements
        for span in page_data.text_spans:
            if span.text:
                origin_y = span.origin_y if span.origin_y is not None else (span.y + span.font_size * 0.88)
                font_lower = span.font_family.lower()
                
                is_bold = (span.font_weight == "bold")
                is_italic = (span.font_style == "italic")
                
                if "courier" in font_lower:
                    if is_bold and is_italic:
                        font_name = "courier-boldoblique"
                    elif is_bold:
                        font_name = "courier-bold"
                    elif is_italic:
                        font_name = "courier-oblique"
                    else:
                        font_name = "courier"
                elif "arial" in font_lower or "helvetica" in font_lower:
                    if is_bold and is_italic:
                        font_name = "hebi"
                    elif is_bold:
                        font_name = "hebo"
                    elif is_italic:
                        font_name = "heit"
                    else:
                        font_name = "helv"
                else:
                    if is_bold and is_italic:
                        font_name = "times-bolditalic"
                    elif is_bold:
                        font_name = "times-bold"
                    elif is_italic:
                        font_name = "times-italic"
                    else:
                        font_name = "times-roman"

                rgb = hex_to_rgb_tuple(span.color) or (0.0, 0.0, 0.0)

                try:
                    page.insert_text(
                        fitz.Point(span.x, origin_y),
                        span.text,
                        fontsize=span.font_size,
                        fontname=font_name,
                        color=rgb
                    )
                except Exception:
                    page.insert_text(
                        fitz.Point(span.x, origin_y),
                        span.text,
                        fontsize=span.font_size,
                        fontname="times-roman",
                        color=rgb
                    )

    pdf_bytes = pdf_out.tobytes(garbage=4, deflate=True)
    pdf_out.close()
    return pdf_bytes

def reconstruct_to_docx_bytes(reconstructed_doc: ReconstructedDocument) -> bytes:
    """
    Exports the reconstructed legal document to an editable Microsoft Word (.docx) file.
    Preserves exact paragraph flow, margins, headings, underlines, two-column signature blocks, and spacing.
    """
    doc = Document()
    
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)

    for p_idx, page in enumerate(reconstructed_doc.pages):
        if p_idx > 0:
            doc.add_page_break()
            
        sorted_spans = sorted(page.text_spans, key=lambda s: (s.y, s.x))
        lines_grouped: List[List[TextElement]] = []
        
        current_line: List[TextElement] = []
        current_y = None
        
        for span in sorted_spans:
            if current_y is None or abs(span.y - current_y) < 5.0:
                current_line.append(span)
                current_y = span.y if current_y is None else current_y
            else:
                lines_grouped.append(sorted(current_line, key=lambda s: s.x))
                current_line = [span]
                current_y = span.y
                
        if current_line:
            lines_grouped.append(sorted(current_line, key=lambda s: s.x))

        prev_bottom_y = None

        for line in lines_grouped:
            line_text = " ".join(s.text for s in line).strip()
            if not line_text:
                continue

            line_y = line[0].y
            line_height = max(s.height for s in line)
            
            # Check if line consists of two distinct columns separated by a large horizontal gap
            is_two_column = False
            left_col_spans: List[TextElement] = []
            right_col_spans: List[TextElement] = []
            
            if len(line) >= 2:
                for idx_s in range(len(line) - 1):
                    gap = line[idx_s + 1].x - (line[idx_s].x + line[idx_s].width)
                    if gap > 60:
                        is_two_column = True
                        left_col_spans = line[:idx_s + 1]
                        right_col_spans = line[idx_s + 1:]
                        break

            # Handle 2-Column signature / multi-party rows via borderless table
            if is_two_column and left_col_spans and right_col_spans:
                table = doc.add_table(rows=1, cols=2)
                table.autofit = False
                table.columns[0].width = Inches(3.4)
                table.columns[1].width = Inches(3.4)
                
                # Left cell
                cell_left = table.cell(0, 0)
                p_l = cell_left.paragraphs[0]
                p_l.paragraph_format.space_before = Pt(4)
                p_l.paragraph_format.space_after = Pt(2)
                p_l.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for s in left_col_spans:
                    r = p_l.add_run(s.text + " ")
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(s.font_size)
                    r.font.bold = (s.font_weight == "bold")
                    r.font.italic = (s.font_style == "italic")
                    r.font.color.rgb = hex_to_docx_rgb(s.color)
                
                # Right cell
                cell_right = table.cell(0, 1)
                p_r = cell_right.paragraphs[0]
                p_r.paragraph_format.space_before = Pt(4)
                p_r.paragraph_format.space_after = Pt(2)
                p_r.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for s in right_col_spans:
                    r = p_r.add_run(s.text + " ")
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(s.font_size)
                    r.font.bold = (s.font_weight == "bold")
                    r.font.italic = (s.font_style == "italic")
                    r.font.color.rgb = hex_to_docx_rgb(s.color)
                    
                prev_bottom_y = line_y + line_height
                continue

            # Standard Paragraph
            p = doc.add_paragraph()
            
            # Preserve vertical delta spacing
            if prev_bottom_y is not None:
                dy = line_y - prev_bottom_y
                if dy > 12:
                    p.paragraph_format.space_before = Pt(min(24, max(4, dy * 0.7)))
                else:
                    p.paragraph_format.space_before = Pt(0)
            else:
                p.paragraph_format.space_before = Pt(0)
                
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            
            # Determine alignment with strict legal accuracy
            total_line_w = sum(s.width for s in line)
            line_left_x = line[0].x
            line_center_x = line_left_x + total_line_w / 2.0
            
            is_centered_heading = (
                any(kw in line_text.upper() for kw in ["FORMAT OF AFFIDAVIT", "DECLARATION", "AFFIDAVIT", "IN THE COURT", "VERSUS", "SUIT NO", "VERIFICATION", "BEFORE THE", "PETITION UNDER", "MEMORANDUM OF"]) or
                (line_text.startswith("(") and ("carefully reading" in line_text.lower() or "please type" in line_text.lower() or "see note" in line_text.lower())) or
                (len(line_text) < 45 and line_left_x > 130 and abs(line_center_x - page.width / 2.0) < 25 and (line[0].font_weight == "bold" or line[0].font_size >= 12 or line_text.isupper()))
            )
            
            is_right_aligned = (
                line_left_x > page.width * 0.58 and len(line_text) < 40 and not is_centered_heading
            )
            
            if is_centered_heading:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif is_right_aligned:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                # Indentation for numbered list items (1., 2., 3., 4., 5., a., b.)
                if re.match(r"^(\d+\.|\([a-z0-9]+\))\s+", line_text):
                    p.paragraph_format.left_indent = Inches(0.2)
                    p.paragraph_format.first_line_indent = Inches(-0.2)
                
            # Add runs for text spans
            for s_idx, span in enumerate(line):
                run = p.add_run(span.text)
                run.font.name = span.font_family if span.font_family in ["Times New Roman", "Arial", "Calibri", "Courier New"] else "Times New Roman"
                run.font.size = Pt(span.font_size)
                run.font.bold = (span.font_weight == "bold")
                run.font.italic = (span.font_style == "italic")
                
                # Check for underline (e.g. AFFIDAVIT heading or legal title underline)
                if span.text.strip().upper() == "AFFIDAVIT" or any(l.y1 > span.y and abs(l.y1 - (span.y + span.height)) < 10 for l in page.lines):
                    if span.text.strip().upper() in ["AFFIDAVIT", "DECLARATION", "UNDERTAKING"]:
                        run.font.underline = True
                        
                run.font.color.rgb = hex_to_docx_rgb(span.color)
                
                if s_idx < len(line) - 1:
                    next_s = line[s_idx + 1]
                    gap = next_s.x - (span.x + span.width)
                    if gap > 12:
                        p.add_run(" " * max(1, int(gap / 6)))
                    else:
                        p.add_run(" ")

            prev_bottom_y = line_y + line_height

    docx_stream = io.BytesIO()
    doc.save(docx_stream)
    docx_stream.seek(0)
    return docx_stream.getvalue()

