import re
from typing import List, Dict, Tuple
from backend.models.document import DocumentPage, FieldElement, TextElement

# Comprehensive legal patterns for template placeholders and blanks
CONSERVATIVE_FIELD_PATTERNS = [
    # 1. Bracketed Template Variables: [ NAME ], [ DATE ], {{CASE_NO}}, <<CLIENT>>, <PLACEHOLDER>
    (r"^\[\s*([A-Za-z0-9_\s]{2,50})\s*\]$", "TEMPLATE_VAR", "Template Variable", 0.98),
    (r"^\{\{\s*([A-Za-z0-9_\s]{2,50})\s*\}\}$", "TEMPLATE_VAR", "Template Variable", 0.98),
    (r"^<<\s*([A-Za-z0-9_\s]{2,50})\s*>>$", "TEMPLATE_VAR", "Template Variable", 0.98),
    (r"^<\s*([A-Za-z0-9_\s]{2,50})\s*>$", "TEMPLATE_VAR", "Template Variable", 0.95),
    
    # 2. Parenthesized Template Variables & Placeholders: e.g. "(date of change of name)", "(old name)", "(new name)", "(Applicant)", "(Deponent)"
    (r"^\(\s*(date\s+of\s+[\w\s]+|old\s+name|new\s+name|name\s+of\s+[\w\s]+|applicant|deponent|father'?s?\s+name|mother'?s?\s+name|spouse'?s?\s+name|address|place|signature|thumb\s+impression|advocate|notary|witness)\s*\)$", "TEMPLATE_VAR", "Template Variable", 0.96),
    (r"^\((?:MR\.?|MS\.?|SH\.?|SMT\.?)?\s*([A-Z\s.]{3,35})\)$", "PARTY_NAME", "Party Name", 0.88),

    # 3. Explicit Underline Blanks with labels: "Name: _________", "Date: ________", "Signature: ________", "residing at _________"
    (r"^(Name|Date|Dated|Signature|Place|Case\s+No|Suit\s+No|Petitioner|Respondent|Lessor|Lessee|Witness|Age|Aadhar\s+No|Passport\s+No|Address)\s*:\s*([_]{2,}|[-]{2,})$", "UNDERLINE_BLANK", "Fillable Blank", 0.95),
    (r"^(?:residing\s+at|aged\s+about|son\s+of|daughter\s+of|wife\s+of|S\/o|D\/o|W\/o)\s+([_]{3,}|[-]{3,})", "UNDERLINE_BLANK", "Fillable Blank", 0.94),
    
    # 4. Explicit Case / Suit Numbers: e.g. "SUIT NO. 452 OF 2026", "CASE NO. ABC/123/2026"
    (r"^(?:SUIT|CASE|PETITION|CRIMINAL\s+MISC|EXECUTION)\s+NO\.\s*[\w\d\/-]+(?:\s+OF\s+\d{4})?$", "CASE_NUMBER", "Case Number", 0.95),
    
    # 5. Explicit Date labels or stand-alone date formats: e.g. "Dated: 12/04/2026", "Date: 12/04/2026"
    (r"^(?:Dated|Date)\s*:\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})$", "DATE", "Date", 0.92),
    
    # 6. Place labels: e.g. "Place: New Delhi"
    (r"^Place\s*:\s*([A-Za-z\s,.-]{3,30})$", "PLACE", "Place", 0.90),

    # 7. Monetary amounts: e.g. "Rs. 100/-", "Rs. 20/-", "INR 500"
    (r"^(?:Rs\.?|INR)\s*[\d,]+(?:\/\-|\.\d{2})?", "AMOUNT", "Monetary Fee / Amount", 0.90),
]

def detect_fields_in_document(pages: List[DocumentPage]) -> Tuple[List[DocumentPage], List[FieldElement]]:
    """
    Performs conservative, high-precision detection of template variables, blanks,
    and fillable legal fields without false-positive classification of normal text.
    """
    global_fields_map: Dict[str, FieldElement] = {}
    
    for page in pages:
        page_fields: List[FieldElement] = []
        
        for span in page.text_spans:
            text = span.text.strip()
            if not text:
                continue
                
            matched = False
            for pattern, field_type, default_label, confidence in CONSERVATIVE_FIELD_PATTERNS:
                match = re.match(pattern, text, re.IGNORECASE)
                if match:
                    matched = True
                    matched_str = text
                    
                    if ":" in matched_str:
                        parts = matched_str.split(":", 1)
                        label = parts[0].strip().upper()
                        val = parts[1].strip() or parts[0].strip()
                    elif matched_str.startswith("(") and matched_str.endswith(")"):
                        inner = matched_str[1:-1].strip()
                        label = inner.upper()
                        val = matched_str
                    elif matched_str.startswith("[") or matched_str.startswith("{{") or matched_str.startswith("<<") or matched_str.startswith("<"):
                        label = match.group(1).strip().upper()
                        val = matched_str
                    else:
                        label = default_label.upper()
                        val = matched_str
                        
                    field_key = f"{label}_{val}".lower()
                    
                    if field_key in global_fields_map:
                        g_field = global_fields_map[field_key]
                        g_field.span_ids.append(span.id)
                        g_field.occurrence_count += 1
                        span.is_field = True
                        span.field_id = g_field.id
                        span.field_type = field_type
                    else:
                        new_field = FieldElement(
                            page=page.page_number,
                            x=span.x,
                            y=span.y,
                            width=span.width,
                            height=span.height,
                            field_type=field_type,
                            label=label,
                            original_text=text,
                            current_text=text,
                            confidence=confidence,
                            editable=True,
                            span_ids=[span.id],
                            occurrence_count=1,
                            z_index=10
                        )
                        global_fields_map[field_key] = new_field
                        page_fields.append(new_field)
                        span.is_field = True
                        span.field_id = new_field.id
                        span.field_type = field_type
                    break
                    
            # Check for standalone line blanks or trailing fillable underscores: e.g. "________", "residing at ________"
            if not matched:
                if re.fullmatch(r"[_]{3,}|[-]{3,}", text):
                    field_key = f"blank_{page.page_number}_{span.id}"
                    new_field = FieldElement(
                        page=page.page_number,
                        x=span.x,
                        y=span.y,
                        width=span.width,
                        height=span.height,
                        field_type="UNDERLINE_BLANK",
                        label="BLANK FILLABLE LINE",
                        original_text=text,
                        current_text=text,
                        confidence=0.96,
                        editable=True,
                        span_ids=[span.id],
                        occurrence_count=1,
                        z_index=10
                    )
                    global_fields_map[field_key] = new_field
                    page_fields.append(new_field)
                    span.is_field = True
                    span.field_id = new_field.id
                    span.field_type = "UNDERLINE_BLANK"
                elif "_" * 3 in text or "-" * 4 in text:
                    # Partial / inline blank within span
                    field_key = f"inline_blank_{page.page_number}_{span.id}"
                    new_field = FieldElement(
                        page=page.page_number,
                        x=span.x,
                        y=span.y,
                        width=span.width,
                        height=span.height,
                        field_type="UNDERLINE_BLANK",
                        label="FILLABLE BLANK",
                        original_text=text,
                        current_text=text,
                        confidence=0.92,
                        editable=True,
                        span_ids=[span.id],
                        occurrence_count=1,
                        z_index=10
                    )
                    global_fields_map[field_key] = new_field
                    page_fields.append(new_field)
                    span.is_field = True
                    span.field_id = new_field.id
                    span.field_type = "UNDERLINE_BLANK"

        page.fields = page_fields
        
    all_global_fields = list(global_fields_map.values())
    return pages, all_global_fields

