"""Detect ruled table cells with OpenCV morphology."""

from typing import Protocol

import cv2
import numpy as np

from pdf_ocr_extractor.models import Rect

MIN_CELL_SIZE = 15
MIN_FILL_RATIO = 0.6
# A ruling-line component must span at least 1/8 of the page's shorter side.
MIN_LINE_EXTENT_DIVISOR = 8


class TableDetector(Protocol):
    def detect(self, binary: np.ndarray) -> tuple[list[Rect], np.ndarray]: ...


def line_mask(binary: np.ndarray) -> np.ndarray:
    """Return a mask (255 = ruling line) of long horizontal/vertical strokes.

    The structuring element is far longer than any glyph stroke, so text is ignored.
    """
    shorter_side = min(binary.shape[:2])
    k = max(40, shorter_side // 40)
    inv = cv2.bitwise_not(binary)
    horizontal = cv2.morphologyEx(inv, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (k, 1)))
    vertical = cv2.morphologyEx(inv, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, k)))
    mask = cv2.dilate(horizontal | vertical, np.ones((3, 3), np.uint8))
    return _keep_long_components(mask, min_extent=shorter_side // MIN_LINE_EXTENT_DIVISOR)


def _keep_long_components(mask: np.ndarray, min_extent: int) -> np.ndarray:
    """Drop line pieces too short to be ruling (e.g. strokes of large glyphs like 工 or 口).

    Short header separators survive because they connect to the long lines of the table grid.
    """
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    keep = [i for i in range(1, count) if max(stats[i][cv2.CC_STAT_WIDTH], stats[i][cv2.CC_STAT_HEIGHT]) >= min_extent]
    return np.where(np.isin(labels, keep), 255, 0).astype(np.uint8)


def cells_from_mask(mask: np.ndarray) -> list[Rect]:
    """Each region enclosed by ruling lines is one connected component of the non-line area."""
    height, width = mask.shape[:2]
    count, _, stats, _ = cv2.connectedComponentsWithStats(cv2.bitwise_not(mask), connectivity=4)
    cells: list[Rect] = []
    for i in range(1, count):
        x, y, w, h, area = (int(v) for v in stats[i])
        touches_border = x == 0 or y == 0 or x + w >= width or y + h >= height
        if touches_border or w < MIN_CELL_SIZE or h < MIN_CELL_SIZE:
            continue
        if area < MIN_FILL_RATIO * w * h:
            continue
        cells.append(Rect(x, y, w, h))
    return sorted(cells, key=lambda c: (c.y, c.x))


def detect_cells(binary: np.ndarray) -> list[Rect]:
    return cells_from_mask(line_mask(binary))


class OpenCvTableDetector:
    def detect(self, binary: np.ndarray) -> tuple[list[Rect], np.ndarray]:
        mask = line_mask(binary)
        return cells_from_mask(mask), mask
