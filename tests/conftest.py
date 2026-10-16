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
    if not as_image:
        return doc.tobytes()
    scanned = pymupdf.open()
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        new = scanned.new_page(width=page.rect.width, height=page.rect.height)
        new.insert_image(new.rect, pixmap=pix)
    return scanned.tobytes()


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
