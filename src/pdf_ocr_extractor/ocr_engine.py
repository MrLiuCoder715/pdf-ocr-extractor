"""Tesseract OCR wrapper producing visual text rows with coordinates."""

from collections.abc import Callable
from typing import Any, Protocol

import cv2
import numpy as np
import pytesseract

from pdf_ocr_extractor.models import OcrLine, OcrWord, Rect
from pdf_ocr_extractor.table_detector import OpenCvTableDetector, TableDetector

ImageToData = Callable[..., dict[str, list[Any]]]
ImageToString = Callable[..., str]

CELL_MARGIN = 2
CELL_PADDING = 20
MIN_INK_PIXELS = 10
CELL_CONFIG = "--psm 7"


class OcrEngine(Protocol):
    def recognize(self, image: np.ndarray, page: int) -> list[OcrLine]: ...


def _words_by_tesseract_line(data: dict[str, list[Any]]) -> list[list[OcrWord]]:
    groups: dict[tuple[int, int, int], list[OcrWord]] = {}
    for i, text in enumerate(data["text"]):
        text = str(text).strip()
        conf = float(data["conf"][i])
        if not text or conf < 0:
            continue
        key = (int(data["block_num"][i]), int(data["par_num"][i]), int(data["line_num"][i]))
        groups.setdefault(key, []).append(
            OcrWord(
                text=text,
                left=int(data["left"][i]),
                top=int(data["top"][i]),
                width=int(data["width"][i]),
                height=int(data["height"][i]),
                conf=conf,
            )
        )
    return list(groups.values())


def _span(words: list[OcrWord]) -> tuple[int, int]:
    return min(w.top for w in words), max(w.top + w.height for w in words)


def _same_row(a: tuple[int, int], b: tuple[int, int], ratio: float) -> bool:
    overlap = min(a[1], b[1]) - max(a[0], b[0])
    shorter = min(a[1] - a[0], b[1] - b[0])
    return shorter > 0 and overlap >= ratio * shorter


def merge_rows(lines: list[list[OcrWord]], overlap_ratio: float = 0.5) -> list[list[OcrWord]]:
    """Merge Tesseract lines whose vertical extents overlap into visual rows."""
    rows: list[list[OcrWord]] = []
    for words in sorted(lines, key=lambda ws: _span(ws)[0]):
        if rows and _same_row(_span(rows[-1]), _span(words), overlap_ratio):
            rows[-1].extend(words)
        else:
            rows.append(list(words))
    return [sorted(row, key=lambda w: w.left) for row in rows]


def tight_crop(binary: np.ndarray, rect: Rect) -> np.ndarray | None:
    """Crop a cell to its ink bounding box plus white padding; None when the cell is blank.

    Tesseract's layout analysis fails on tall, mostly empty cells, so the crop matters.
    """
    m = CELL_MARGIN
    crop = binary[rect.y + m : rect.y + rect.h - m, rect.x + m : rect.x + rect.w - m]
    ys, xs = np.nonzero(crop < 128)
    if len(xs) < MIN_INK_PIXELS:
        return None
    ink = crop[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    return cv2.copyMakeBorder(ink, *([CELL_PADDING] * 4), cv2.BORDER_CONSTANT, value=255)


class TesseractOcrEngine:
    """Ruled table cells are OCRed one by one; the rest of the page in a single pass."""

    def __init__(
        self,
        lang: str,
        tesseract_cmd: str | None = None,
        image_to_data: ImageToData | None = None,
        image_to_string: ImageToString | None = None,
        detector: TableDetector | None = None,
    ) -> None:
        self.lang = lang
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self._image_to_data = image_to_data or pytesseract.image_to_data
        self._image_to_string = image_to_string or pytesseract.image_to_string
        self._detector = detector or OpenCvTableDetector()

    def recognize(self, image: np.ndarray, page: int) -> list[OcrLine]:
        cells, mask = self._detector.detect(image)
        groups = _words_by_tesseract_line(self._page_data(image, cells, mask))
        groups.extend([word] for word in self._cell_words(image, cells))
        return [OcrLine(page=page, words=row) for row in merge_rows(groups)]

    def _page_data(self, image: np.ndarray, cells: list[Rect], mask: np.ndarray) -> dict[str, list[Any]]:
        outside = image.copy()
        outside[mask > 0] = 255
        for c in cells:
            outside[c.y : c.y + c.h, c.x : c.x + c.w] = 255
        return self._image_to_data(outside, lang=self.lang, output_type=pytesseract.Output.DICT)

    def _cell_words(self, image: np.ndarray, cells: list[Rect]) -> list[OcrWord]:
        words = []
        for c in cells:
            crop = tight_crop(image, c)
            if crop is None:
                continue
            text = " ".join(self._image_to_string(crop, lang=self.lang, config=CELL_CONFIG).split())
            if text:
                # image_to_string reports no confidence; 0.0 marks it as unknown.
                words.append(OcrWord(text, c.x, c.y, c.w, c.h, conf=0.0, in_table=True))
        return words
