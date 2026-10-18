import shutil

import pymupdf
import pytest


def make_pdf(pages: list[list[str]], *, as_image: bool = True) -> bytes:
    """Build a PDF whose pages carry the given text lines.

    With ``as_image`` the text is rasterised so the PDF has no text layer,
    forcing the OCR path like a scanned document.
    """
    doc = pymupdf.open()
    for lines in pages:
        page = doc.new_page(width=595, height=842)
        for i, text in enumerate(lines):
            page.insert_text((60, 100 + i * 50), text, fontname="china-t", fontsize=22)
    return doc.tobytes() if not as_image else _rasterize(doc, dpi=200)


def _rasterize(doc: pymupdf.Document, dpi: int) -> bytes:
    """Replace every page by a PNG of itself, like a scanned document."""
    scanned = pymupdf.open()
    for page in doc:
        png = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY).tobytes("png")
        new = scanned.new_page(width=page.rect.width, height=page.rect.height)
        new.insert_image(new.rect, stream=png)
    return scanned.tobytes(deflate=True)


# Roster layout modelled on a real staff list; all names are fictitious.
ROSTER_LABELS = [
    ("承商名稱", "測試公司"),
    ("工程編號", ""),
    ("契約編號", "21915A451"),
    ("契約名稱", "115年度寬頻網路設備建設案"),
]
ROSTER_PAGES = [
    [("1", ""), ("2", "王小明")],
    [("3", "陳大華"), ("4", "林志玲"), ("5", "張三豐")],
    [("6", "李四海"), ("7", "趙六安"), ("8", "周七星")],
]
ROSTER_NAMES = [name for page in ROSTER_PAGES for _, name in page if name]


def make_roster_pdf() -> bytes:
    """Labels on top, then a ruled 項次|姓 名|大頭照 table continuing over 3 pages (no repeated header)."""
    cols = (219, 279, 340, 627)
    row_h, fs = 133, 10.5
    doc = pymupdf.open()
    for p, rows in enumerate(ROSTER_PAGES):
        page = doc.new_page(width=842, height=595)
        y = 100
        if p == 0:
            for i, (label, value) in enumerate(ROSTER_LABELS):
                page.insert_text((222, 126 + i * 15), label, fontname="china-t", fontsize=fs)
                if value:
                    page.insert_text((283, 126 + i * 15), value, fontname="china-t", fontsize=fs)
            for (a, b), text in zip(zip(cols, cols[1:]), ("項次", "姓 名", "大頭照")):
                page.draw_rect(pymupdf.Rect(a, 183, b, 213), width=1.2)
                page.insert_text(((a + b) / 2 - len(text) * fs / 2, 203), text, fontname="china-t", fontsize=fs)
            y = 213
        for num, name in rows:
            for a, b in zip(cols, cols[1:]):
                page.draw_rect(pymupdf.Rect(a, y, b, y + row_h), width=1.2)
            page.insert_text((246, y + row_h / 2 + 4), num, fontname="china-t", fontsize=fs)
            if name:
                page.insert_text((294, y + row_h / 2 + 4), name, fontname="china-t", fontsize=fs)
            # stand-in for the ID photo
            page.draw_rect(pymupdf.Rect(430, y + 2, 540, y + row_h - 2), color=(0.4, 0.4, 0.4), fill=(0.6, 0.6, 0.6))
            y += row_h
    return _rasterize(doc, dpi=150)


@pytest.fixture
def pdf_factory():
    return make_pdf


def pytest_collection_modifyitems(config, items):
    if shutil.which("tesseract"):
        return
    skip = pytest.mark.skip(reason="tesseract binary not available (run tests in Docker)")
    for item in items:
        if "tesseract" in item.keywords:
            item.add_marker(skip)
