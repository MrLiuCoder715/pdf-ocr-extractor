import cv2
import numpy as np

from pdf_ocr_extractor.table_detector import detect_cells, line_mask


def blank(h=600, w=900):
    return np.full((h, w), 255, dtype=np.uint8)


def draw_grid(img, x0, y0, col_w, row_h, cols, rows, thickness=3):
    for r in range(rows + 1):
        y = y0 + r * row_h
        cv2.line(img, (x0, y), (x0 + cols * col_w, y), 0, thickness)
    for c in range(cols + 1):
        x = x0 + c * col_w
        cv2.line(img, (x, y0), (x, y0 + rows * row_h), 0, thickness)


def test_detects_every_cell_of_2x3_table():
    img = blank()
    draw_grid(img, 100, 100, 200, 150, cols=3, rows=2)
    cells = detect_cells(img)
    assert len(cells) == 6
    for c in cells:
        assert 100 <= c.x and c.x + c.w <= 700
        assert 100 <= c.y and c.y + c.h <= 400
        assert 150 < c.w < 200 and 100 < c.h < 150


def test_cells_sorted_top_to_bottom_then_left_to_right():
    img = blank()
    draw_grid(img, 100, 100, 200, 150, cols=3, rows=2)
    cells = detect_cells(img)
    assert [c.x < cells[i + 1].x for i, c in enumerate(cells[:2])] == [True, True]
    assert cells[0].y < cells[3].y


def test_page_without_lines_has_no_cells():
    img = blank()
    cv2.putText(img, "Hello World 12345", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 2, 0, 4)
    assert detect_cells(img) == []


def test_text_inside_cells_does_not_create_extra_cells():
    img = blank()
    draw_grid(img, 100, 100, 200, 150, cols=3, rows=2)
    for i in range(3):
        cv2.putText(img, "HI", (140 + i * 200, 190), cv2.FONT_HERSHEY_SIMPLEX, 1.5, 0, 3)
        cv2.putText(img, "|", (160 + i * 200, 340), cv2.FONT_HERSHEY_SIMPLEX, 1.5, 0, 3)
    assert len(detect_cells(img)) == 6


def draw_large_glyphs(img, x, y, size=90):
    """Strokes of large characters (工 and 口) are longer than the line kernel."""
    cv2.line(img, (x, y), (x + size, y), 0, 6)                       # 工: top bar
    cv2.line(img, (x + size // 2, y), (x + size // 2, y + size), 0, 6)
    cv2.line(img, (x, y + size), (x + size, y + size), 0, 6)         # 工: bottom bar
    cv2.rectangle(img, (x + 150, y), (x + 150 + size, y + size), 0, 6)  # 口: closed box


def test_large_glyph_strokes_are_not_lines_or_cells():
    img = blank(1000, 1400)
    draw_large_glyphs(img, 100, 100)
    assert detect_cells(img) == []
    assert not line_mask(img).any()


def test_table_still_found_next_to_large_glyphs():
    img = blank(1000, 1400)
    draw_large_glyphs(img, 100, 100)
    draw_grid(img, 100, 400, 300, 60, cols=3, rows=3)   # short 60px header-like separators
    assert len(detect_cells(img)) == 9
