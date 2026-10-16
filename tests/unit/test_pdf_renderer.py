import numpy as np
import pytest

from pdf_ocr_extractor.pdf_renderer import InvalidPdfError, PyMuPdfRenderer


def test_renders_every_page_in_order(pdf_factory):
    pdf = pdf_factory([["page one"], ["page two"], ["page three"]], as_image=False)
    images = PyMuPdfRenderer(dpi=72, max_pages=20).render(pdf)
    assert len(images) == 3
    assert all(isinstance(img, np.ndarray) and img.ndim == 3 and img.shape[2] == 3 for img in images)


def test_dpi_controls_image_size(pdf_factory):
    pdf = pdf_factory([["x"]], as_image=False)
    low = PyMuPdfRenderer(dpi=72, max_pages=20).render(pdf)[0]
    high = PyMuPdfRenderer(dpi=144, max_pages=20).render(pdf)[0]
    assert high.shape[0] == pytest.approx(low.shape[0] * 2, abs=2)


def test_respects_max_pages(pdf_factory):
    pdf = pdf_factory([["a"], ["b"], ["c"]], as_image=False)
    assert len(PyMuPdfRenderer(dpi=72, max_pages=2).render(pdf)) == 2


def test_invalid_pdf_raises():
    with pytest.raises(InvalidPdfError):
        PyMuPdfRenderer(dpi=72, max_pages=20).render(b"not a pdf")
