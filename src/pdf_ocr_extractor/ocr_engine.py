"""Tesseract OCR wrapper producing visual text rows with coordinates."""

from collections.abc import Callable
from typing import Any, Protocol

import numpy as np
import pytesseract

from pdf_ocr_extractor.models import OcrLine, OcrWord

ImageToData = Callable[..., dict[str, list[Any]]]


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


class TesseractOcrEngine:
    def __init__(
        self,
        lang: str,
        tesseract_cmd: str | None = None,
        image_to_data: ImageToData | None = None,
    ) -> None:
        self.lang = lang
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self._image_to_data = image_to_data or pytesseract.image_to_data

    def recognize(self, image: np.ndarray, page: int) -> list[OcrLine]:
        data = self._image_to_data(image, lang=self.lang, output_type=pytesseract.Output.DICT)
        return [OcrLine(page=page, words=row) for row in merge_rows(_words_by_tesseract_line(data))]
