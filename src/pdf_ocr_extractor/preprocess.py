"""OpenCV image clean-up before OCR."""

from typing import Protocol

import cv2
import numpy as np


class ImagePreprocessor(Protocol):
    def process(self, image: np.ndarray) -> np.ndarray: ...


class OpenCvPreprocessor:
    """Grayscale -> median denoise -> Otsu binarisation."""

    def __init__(self, blur_kernel: int = 3) -> None:
        self.blur_kernel = blur_kernel

    def process(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
        denoised = cv2.medianBlur(gray, self.blur_kernel)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
