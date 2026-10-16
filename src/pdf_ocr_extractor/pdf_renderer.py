"""Render PDF pages to RGB numpy images."""

from typing import Protocol

import numpy as np
import pymupdf


class InvalidPdfError(ValueError):
    """Raised when the input bytes are not a readable PDF."""


class PdfRenderer(Protocol):
    def render(self, pdf_bytes: bytes) -> list[np.ndarray]: ...


class PyMuPdfRenderer:
    def __init__(self, dpi: int, max_pages: int) -> None:
        self.dpi = dpi
        self.max_pages = max_pages

    def render(self, pdf_bytes: bytes) -> list[np.ndarray]:
        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        except (RuntimeError, ValueError) as exc:
            raise InvalidPdfError(str(exc)) from exc
        with doc:
            if not doc.is_pdf or doc.page_count == 0:
                raise InvalidPdfError("PDF has no pages")
            return [self._to_array(doc[i]) for i in range(min(doc.page_count, self.max_pages))]

    def _to_array(self, page: pymupdf.Page) -> np.ndarray:
        pix = page.get_pixmap(dpi=self.dpi, colorspace=pymupdf.csRGB, alpha=False)
        buf = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.stride)
        return buf[:, : pix.width * pix.n].reshape(pix.height, pix.width, pix.n).copy()
