import io
import os
import re
import json
import base64
import shutil
from typing import List, Tuple, Optional
from dotenv import load_dotenv
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import fitz  # PyMuPDF
from backend.models.document import TextSpan, LineElement

# Load environment variables (.env)
load_dotenv()

# Configure Tesseract binary path
TESSERACT_PATHS = [
    "/opt/homebrew/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/usr/bin/tesseract",
    shutil.which("tesseract") or ""
]
TESSERACT_CMD = next((p for p in TESSERACT_PATHS if p and os.path.exists(p)), None)

# Circuit breaker flag to avoid repeated timeouts if API quota is exhausted
GEMINI_QUOTA_EXHAUSTED = False

def is_page_scanned(page: fitz.Page) -> bool:
    """
    Determines if a page is purely scanned / image-based with minimal selectable text.
    """
    text = page.get_text("text").strip()
    images = page.get_images()
    
    # If text is virtually empty (< 15 chars) but has images or drawings, it's scanned
    if len(text) < 15 and len(images) > 0:
        return True
    
    # If there is no selectable text at all
    if len(text) == 0:
        return True
        
    return False

def remove_pen_ink_from_image(pil_img: Image.Image) -> Tuple[Image.Image, int]:
    """
    Detects and removes handwritten pen ink (blue ballpoint, gel pen, cyan, purple, red, green)
    from a scanned legal document, preserving the black printed template and table borders.
    """
    rgb = pil_img.convert("RGB")
    arr = np.array(rgb, dtype=np.int16)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    
    # 1. Blue / Cyan / Violet Ballpoint & Gel Pen Ink (Dominant in legal forms)
    is_blue_ink = (b - r > 8) & (b - g > 5) & (b > 30)
    
    # 2. Cyan / Light Blue Pen
    is_cyan_ink = (b + g - 2 * r > 15) & (b > 45) & (g > 45) & (r < 210)
    
    # 3. Purple / Magenta Pen
    is_purple_ink = (r > 45) & (b > 45) & (g < r - 6) & (g < b - 6)
    
    # 4. Red Pen
    is_red_ink = (r - b > 18) & (r - g > 12) & (r > 45)
    
    # 5. Green Pen
    is_green_ink = (g - r > 12) & (g - b > 12) & (g > 40)
    
    pen_mask = is_blue_ink | is_cyan_ink | is_purple_ink | is_red_ink | is_green_ink
    pen_pixel_count = int(np.sum(pen_mask))
    
    if pen_pixel_count == 0:
        return pil_img, 0
        
    clean_arr = arr.copy()
    clean_arr[pen_mask] = [255, 255, 255]
    
    # Dilate pen mask slightly to eliminate antialiased ink edge fringes
    mask_img = Image.fromarray((pen_mask * 255).astype(np.uint8), mode="L")
    dilated_mask = mask_img.filter(ImageFilter.MaxFilter(3))
    dilated_mask_arr = np.array(dilated_mask) > 128
    
    # Only clean light-to-mid ink fringes, never pure black toner
    is_light_fringe = dilated_mask_arr & ((r + g + b) // 3 > 70)
    clean_arr[is_light_fringe] = [255, 255, 255]
    
    return Image.fromarray(np.clip(clean_arr, 0, 255).astype(np.uint8)), pen_pixel_count

def detect_image_grid_lines(clean_img: Image.Image, page_w: float, page_h: float, page_num: int = 1) -> List[LineElement]:
    """
    Extracts table borders, column separators, and horizontal rules from a scanned document image.
    """
    gray = np.array(clean_img.convert("L"))
    img_h, img_w = gray.shape
    dark = (gray < 200).astype(np.int32)
    
    scale_x = page_w / img_w
    scale_y = page_h / img_h
    
    # Horizontal lines (check continuous dark runs)
    h_lines_raw = []
    min_h_len = max(25, int(img_w * 0.10))
    for y in range(img_h):
        row = dark[y]
        diff = np.diff(np.pad(row, (1, 1), 'constant'))
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0]
        for s, e in zip(starts, ends):
            if (e - s) >= min_h_len:
                h_lines_raw.append({'y': y, 'x1': int(s), 'x2': int(e)})
                
    # Vertical lines
    v_lines_raw = []
    min_v_len = max(20, int(img_h * 0.03))
    for x in range(img_w):
        col = dark[:, x]
        diff = np.diff(np.pad(col, (1, 1), 'constant'))
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0]
        for s, e in zip(starts, ends):
            if (e - s) >= min_v_len:
                v_lines_raw.append({'x': x, 'y1': int(s), 'y2': int(e)})
                
    # Merge nearby horizontal lines
    merged_h = []
    h_lines_raw.sort(key=lambda item: item['y'])
    for item in h_lines_raw:
        if not merged_h or abs(item['y'] - merged_h[-1]['y']) > 4:
            merged_h.append(item.copy())
        else:
            merged_h[-1]['x1'] = min(merged_h[-1]['x1'], item['x1'])
            merged_h[-1]['x2'] = max(merged_h[-1]['x2'], item['x2'])
            
    # Merge nearby vertical lines
    merged_v = []
    v_lines_raw.sort(key=lambda item: item['x'])
    for item in v_lines_raw:
        if not merged_v or abs(item['x'] - merged_v[-1]['x']) > 4:
            merged_v.append(item.copy())
        else:
            merged_v[-1]['y1'] = min(merged_v[-1]['y1'], item['y1'])
            merged_v[-1]['y2'] = max(merged_v[-1]['y2'], item['y2'])
            
    vector_lines: List[LineElement] = []
    
    for h in merged_h:
        x1_pt = round(h['x1'] * scale_x, 2)
        y_pt = round(h['y'] * scale_y, 2)
        x2_pt = round(h['x2'] * scale_x, 2)
        w_pt = round(x2_pt - x1_pt, 2)
        if w_pt > 15:
            vector_lines.append(LineElement(
                page=page_num,
                x=x1_pt,
                y=y_pt,
                width=w_pt,
                height=1.0,
                x1=x1_pt,
                y1=y_pt,
                x2=x2_pt,
                y2=y_pt,
                line_width=1.0,
                color="#000000",
                z_index=1
            ))
            
    for v in merged_v:
        x_pt = round(v['x'] * scale_x, 2)
        y1_pt = round(v['y1'] * scale_y, 2)
        y2_pt = round(v['y2'] * scale_y, 2)
        h_pt = round(y2_pt - y1_pt, 2)
        if h_pt > 15:
            vector_lines.append(LineElement(
                page=page_num,
                x=x_pt,
                y=y1_pt,
                width=1.0,
                height=h_pt,
                x1=x_pt,
                y1=y1_pt,
                x2=x_pt,
                y2=y2_pt,
                line_width=1.0,
                color="#000000",
                z_index=1
            ))
            
    return vector_lines

def clean_legal_ocr_text(text: str) -> str:
    """Repairs common OCR optical misreads on legal documents."""
    t = text
    # Strip stray OCR quote prefixes on headings: e.g. "‘NAME" -> "NAME", "‘COURT" -> "COURT"
    t = re.sub(r"^[‘'\"`\[|]\s*", "", t)
    t = re.sub(r"\s*[’'\"`\]|]$", "", t)
    t = re.sub(r"^(\d+)[,;]\s*", r"\1. ", t)
    t = re.sub(r"(\s|^)[|\[]($|\s)", r"\1I\2", t)
    t = re.sub(r"(\s|^)[|\[]have\b", r"\1I have", t)
    t = re.sub(r"(\s|^)[|\[]am\b", r"\1I am", t)
    t = re.sub(r"(\s|^)[|\[]state\b", r"\1I state", t)
    t = re.sub(r"(\s|^)[|\[]hereby\b", r"\1I hereby", t)
    t = re.sub(r"\bWe son/daughter\b", "I, ________ son/daughter", t, flags=re.I)
    t = re.sub(r"\b1,\s*son/daughter\b", "I, ________ son/daughter", t, flags=re.I)
    t = re.sub(r"\bmame\b", "name", t, flags=re.I)
    t = re.sub(r"\bwnder\b", "under", t, flags=re.I)
    t = re.sub(r"\bard\b", "and", t, flags=re.I)
    t = re.sub(r"\bSUTT\b", "SUIT", t, flags=re.I)
    t = re.sub(r"\bSUT\b", "SUIT", t, flags=re.I)
    t = re.sub(r"\bdete of change\b", "date of change", t, flags=re.I)
    t = re.sub(r"\b5\.E\.,?0\.\b", "S.E.O.", t)
    t = re.sub(r"\bCommisstoner\b", "Commissioner", t)
    t = re.sub(r"\bNotary/S\.[£f]\.0\b", "Notary/S.E.O.", t)
    t = re.sub(r"\bOn this day of 20 i\]", "On this ___ day of _____ 20  )", t)
    t = re.sub(r"\bSolemnly affirmed at \]\s*", "Solemnly affirmed at ________  )", t)
    t = re.sub(r"\bSolemnly affirmed at J\s*", "Solemnly affirmed at ________  )", t)
    return t.strip()

def ocr_with_tesseract(page: fitz.Page, page_num: int, ignore_pen_ink: bool = True) -> Tuple[List[TextSpan], List[LineElement]]:
    """
    Extracts text spans and table grid lines using Tesseract OCR.
    If ignore_pen_ink=True, strips out pen handwriting and copies the clean printed template & grid.
    """
    import pytesseract
    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

    pix = page.get_pixmap(dpi=220)
    raw_img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    
    # 1. Pen Ink Filtering (Ignores ballpoint/gel pen handwriting, preserves printed layout)
    if ignore_pen_ink:
        proc_img, _ = remove_pen_ink_from_image(raw_img)
    else:
        proc_img = raw_img

    # 2. Extract Table Grid Lines from the clean image
    grid_lines = detect_image_grid_lines(proc_img, page.rect.width, page.rect.height, page_num)

    # 3. Image enhancement for character recognition
    gray_img = proc_img.convert("L")
    enhancer = ImageEnhance.Contrast(gray_img)
    enhanced_img = enhancer.enhance(1.8)
    
    scale_x = page.rect.width / pix.width
    scale_y = page.rect.height / pix.height

    # Run Tesseract with sparse text / form detection mode (PSM 11)
    data = pytesseract.image_to_data(enhanced_img, config="--psm 11", output_type=pytesseract.Output.DICT)
    n_boxes = len(data['text'])
    
    # Group words by spatial lines (vertical closeness < 6px)
    valid_words = []
    for i in range(n_boxes):
        word = data['text'][i].strip()
        conf = int(data['conf'][i])
        
        if conf > 0 and word and len(word) > 0 and not re.match(r"^[_\.\-=~|/\\]+$", word):
            valid_words.append({
                'text': word,
                'left': data['left'][i],
                'top': data['top'][i],
                'width': data['width'][i],
                'height': data['height'][i],
                'font_size': data['height'][i] * scale_y * 0.85
            })

    # Sort top to bottom, left to right
    valid_words.sort(key=lambda w: (w['top'], w['left']))
    
    # Group into lines by y-coordinate
    lines: List[List[dict]] = []
    for w in valid_words:
        assigned = False
        for line in lines:
            avg_top = sum(item['top'] for item in line) / len(line)
            avg_height = sum(item['height'] for item in line) / len(line)
            if abs(w['top'] - avg_top) < max(6.0, avg_height * 0.6):
                line.append(w)
                assigned = True
                break
        if not assigned:
            lines.append([w])

    spans: List[TextSpan] = []
    vector_lines: List[LineElement] = list(grid_lines)
    span_idx = 0
    
    for l_idx, words in enumerate(lines):
        if not words:
            continue
            
        words.sort(key=lambda item: item['left'])
            
        # Split line into chunks if separated by table column gaps (> 35px)
        word_chunks = []
        current_chunk = [words[0]]
        for w in words[1:]:
            prev_w = current_chunk[-1]
            gap = w['left'] - (prev_w['left'] + prev_w['width'])
            if gap > 35:  # Separate table cell or column
                word_chunks.append(current_chunk)
                current_chunk = [w]
            else:
                current_chunk.append(w)
        if current_chunk:
            word_chunks.append(current_chunk)
            
        for chunk in word_chunks:
            raw_line_text = " ".join(w['text'] for w in chunk).strip()
            if not raw_line_text:
                continue
                
            full_line_text = clean_legal_ocr_text(raw_line_text)
            if not full_line_text:
                continue
                
            min_left = min(w['left'] for w in chunk)
            min_top = min(w['top'] for w in chunk)
            max_right = max(w['left'] + w['width'] for w in chunk)
            max_bottom = max(w['top'] + w['height'] for w in chunk)
            
            x = min_left * scale_x
            y = min_top * scale_y
            w = (max_right - min_left) * scale_x
            h = (max_bottom - min_top) * scale_y
            
            font_size = round(max(8.5, min(16.0, h * 0.85)), 1)
            is_bold = any(kw in full_line_text.upper() for kw in [
                "CHECK-LIST", "CHECKLIST", "VALUATION", "JURISDICTION", "NAME & ADDRESS",
                "NATURE OF SUIT", "AGE OF PARTIES", "WHETHER ANY", "CAVEAT", "COURT FEE",
                "CONNECTED CASES", "AFFIDAVIT", "SUIT NO", "IN THE COURT", "VERSUS",
                "PLAINTIFF", "DEFENDANT", "DECLARATION", "NOTES:"
            ])
            is_italic = "carefully reading" in full_line_text.lower() or full_line_text.startswith("(")
            
            spans.append(TextSpan(
                text=full_line_text,
                original_text=full_line_text,
                x=round(x, 2),
                y=round(y, 2),
                width=round(w, 2),
                height=round(h, 2),
                origin_y=round(y + h, 2),
                font_family="Times New Roman",
                font_size=font_size,
                font_weight="bold" if is_bold else "normal",
                font_style="italic" if is_italic else "normal",
                color="#000000",
                block_index=l_idx,
                line_index=l_idx,
                span_index=span_idx
            ))
            
            span_idx += 1
        
    return spans, vector_lines

def ocr_with_gemini(page: fitz.Page, page_num: int, ignore_pen_ink: bool = True) -> Tuple[List[TextSpan], List[LineElement]]:
    """Extracts high-fidelity legal document template text with Google Gemini Vision."""
    global GEMINI_QUOTA_EXHAUSTED
    if GEMINI_QUOTA_EXHAUSTED:
        return [], []
        
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return [], []

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        pix = page.get_pixmap(dpi=180)
        raw_img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        if ignore_pen_ink:
            proc_img, _ = remove_pen_ink_from_image(raw_img)
        else:
            proc_img = raw_img
            
        buf = io.BytesIO()
        proc_img.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        
        prompt = (
            "You are a master legal document template extractor. Extract the clean printed layout of this legal document image.\n"
            "CRITICAL REQUIREMENT:\n"
            "1. Ignore any handwritten pen notes, handwriting, or filled signatures. Extract ONLY the printed template text, headings, clauses, table headers, column labels, numbers, and fillable blank lines.\n"
            "2. Preserve all fillable blank underscores EXACTLY as they appear.\n"
            "3. Return a JSON object: {\"lines\": [{\"text\": \"string\", \"box_2d\": [ymin, xmin, ymax, xmax], \"font_size_pt\": 11, \"is_bold\": false, \"is_italic\": false}], \"rules\": [{\"box_2d\": [ymin, xmin, ymax, xmax]}]}.\n"
            "box_2d coordinates must be normalized integers on a 0 to 1000 scale."
        )
        
        response = None
        for model_name in ['gemini-2.5-flash', 'gemini-3.5-flash']:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        genai.types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                        prompt
                    ],
                    config=genai.types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                if response and response.text:
                    break
            except Exception as model_err:
                err_str = str(model_err)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    print(f"[OCR] Gemini API quota reached: disabling Gemini and switching permanently to local Tesseract.")
                    GEMINI_QUOTA_EXHAUSTED = True
                    return [], []
                print(f"[OCR] Model {model_name} attempt skipped: {model_err}")
                continue
                
        if not response or not response.text:
            return [], []
            
        resp_text = response.text.strip()
        data = json.loads(resp_text)
        
        items = data.get("lines", data.get("elements", [])) if isinstance(data, dict) else []
        rules = data.get("rules", []) if isinstance(data, dict) else []
            
        spans: List[TextSpan] = []
        vector_lines: List[LineElement] = []
        
        for idx, item in enumerate(items):
            if isinstance(item, dict):
                box = item.get("box_2d", [0, 0, 0, 0])
                font_sz = float(item.get("font_size_pt", 11.0))
                is_b = bool(item.get("is_bold", False))
                is_i = bool(item.get("is_italic", False))
                txt = str(item.get("text", "")).strip()
            else:
                continue

            if not txt:
                continue
                
            ymin, xmin, ymax, xmax = box[0], box[1], box[2], box[3]
            x = (xmin / 1000.0) * page.rect.width
            y = (ymin / 1000.0) * page.rect.height
            w = max(10.0, ((xmax - xmin) / 1000.0) * page.rect.width)
            h = max(8.0, ((ymax - ymin) / 1000.0) * page.rect.height)
            
            computed_font_size = round(max(8.5, min(font_sz, h * 0.88)), 1)
            
            spans.append(TextSpan(
                text=txt,
                original_text=txt,
                x=round(x, 2),
                y=round(y, 2),
                width=round(w, 2),
                height=round(h, 2),
                origin_y=round(y + h, 2),
                font_family="Times New Roman",
                font_size=computed_font_size,
                font_weight="bold" if is_b else "normal",
                font_style="italic" if is_i else "normal",
                color="#000000",
                block_index=idx,
                line_index=idx,
                span_index=idx
            ))
            
            span_idx = idx + 1
            
        for r_idx, rule in enumerate(rules):
            if isinstance(rule, dict) and "box_2d" in rule:
                r_box = rule["box_2d"]
                ry, rx, _, rx_max = r_box[0], r_box[1], r_box[2], r_box[3]
                rx_pt = (rx / 1000.0) * page.rect.width
                ry_pt = (ry / 1000.0) * page.rect.height
                rw_pt = ((rx_max - rx) / 1000.0) * page.rect.width
                vector_lines.append(LineElement(
                    page=page_num,
                    x=round(rx_pt, 2),
                    y=round(ry_pt, 2),
                    width=round(rw_pt, 2),
                    height=1.0,
                    x1=round(rx_pt, 2),
                    y1=round(ry_pt, 2),
                    x2=round(rx_pt + rw_pt, 2),
                    y2=round(ry_pt, 2),
                    line_width=1.0,
                    color="#000000",
                    z_index=1
                ))
            
        return spans, vector_lines
    except Exception as e:
        print(f"[OCR] Gemini Vision OCR failed: {e}")
        return [], []

def ocr_page_to_spans(page: fitz.Page, page_num: int, ignore_pen_ink: bool = True) -> Tuple[List[TextSpan], List[LineElement], bool]:
    """
    Performs OCR on a scanned page and returns structured TextSpans and vector LineElements.
    Supports automatic pen-ink removal to copy the clean printed legal template.
    """
    # Method 1: Google Gemini Vision AI (if quota not exhausted)
    if not GEMINI_QUOTA_EXHAUSTED:
        try:
            gemini_spans, gemini_lines = ocr_with_gemini(page, page_num, ignore_pen_ink=ignore_pen_ink)
            if gemini_spans and len(gemini_spans) > 0:
                return gemini_spans, gemini_lines, True
        except Exception as e:
            print(f"[OCR] Gemini OCR error: {e}")

    # Method 2: Enhanced Local Tesseract OCR with Pen Filter & Table Grid Detection
    try:
        tess_spans, tess_lines = ocr_with_tesseract(page, page_num, ignore_pen_ink=ignore_pen_ink)
        if tess_spans and len(tess_spans) > 0:
            return tess_spans, tess_lines, True
    except Exception as e:
        print(f"[OCR] Tesseract error: {e}")

    return [], [], False
