import io
import pytest
import numpy as np
from PIL import Image, ImageDraw
from backend.pdf_processor.ocr import remove_pen_ink_from_image, detect_image_grid_lines

def test_pen_ink_removal_filters_blue_and_red_ink():
    # Create synthetic test page: white background with black printed text, black table grid, and blue pen handwriting
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 1. Black printed text and borders
    draw.line([(50, 50), (550, 50)], fill=(0, 0, 0), width=2)
    draw.line([(50, 50), (50, 400)], fill=(0, 0, 0), width=2)
    draw.line([(550, 50), (550, 400)], fill=(0, 0, 0), width=2)
    draw.line([(50, 400), (550, 400)], fill=(0, 0, 0), width=2)
    draw.text((70, 70), "CHECK-LIST", fill=(0, 0, 0))
    draw.text((70, 120), "VALUATION OF SUIT:", fill=(0, 0, 0))
    
    # 2. Blue pen handwriting (e.g. ballpoint/gel pen)
    draw.text((250, 120), "Rs. 260/- (Paid by Advocate)", fill=(20, 50, 210))
    draw.line([(240, 140), (450, 140)], fill=(30, 60, 200), width=2)
    
    # 3. Red pen annotation
    draw.text((70, 300), "VERIFIED BY COURT", fill=(210, 30, 30))
    
    # Run pen ink removal
    clean_img, pen_pixels = remove_pen_ink_from_image(img)
    assert pen_pixels > 0
    
    clean_arr = np.array(clean_img)
    # The blue pen area should now be white (255, 255, 255)
    # Check pixel where blue line was
    assert clean_arr[140, 300, 0] > 240
    assert clean_arr[140, 300, 1] > 240
    assert clean_arr[140, 300, 2] > 240
    
    # The black border should remain intact
    assert clean_arr[50, 200, 0] < 50

def test_detect_image_grid_lines():
    img = Image.new("RGB", (500, 700), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw horizontal and vertical grid lines
    draw.line([(50, 100), (450, 100)], fill=(0, 0, 0), width=2)
    draw.line([(50, 200), (450, 200)], fill=(0, 0, 0), width=2)
    draw.line([(50, 100), (50, 600)], fill=(0, 0, 0), width=2)
    draw.line([(250, 100), (250, 600)], fill=(0, 0, 0), width=2)
    draw.line([(450, 100), (450, 600)], fill=(0, 0, 0), width=2)
    
    lines = detect_image_grid_lines(img, 500.0, 700.0)
    assert len(lines) >= 3
    # Check that both horizontal and vertical lines are detected
    has_h = any(l.width > 200 for l in lines)
    has_v = any(l.height > 200 for l in lines)
    assert has_h
    assert has_v
