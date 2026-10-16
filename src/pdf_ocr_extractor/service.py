"""Orchestrates render -> preprocess -> OCR -> field extraction for one PDF."""

from collections.abc import Sequence

from pdf_ocr_extractor.field_extractor import extract_fields
from pdf_ocr_extractor.models import ExtractionResult, OcrLine
from pdf_ocr_extractor.ocr_engine import OcrEngine
from pdf_ocr_extractor.pdf_renderer import PdfRenderer
from pdf_ocr_extractor.preprocess import ImagePreprocessor


class ExtractionService:
    def __init__(self, renderer: PdfRenderer, preprocessor: ImagePreprocessor, ocr: OcrEngine) -> None:
        self.renderer = renderer
        self.preprocessor = preprocessor
        self.ocr = ocr

    def extract(self, pdf_bytes: bytes, filename: str, titles: Sequence[str]) -> ExtractionResult:
        lines: list[OcrLine] = []
        for page_no, image in enumerate(self.renderer.render(pdf_bytes), start=1):
            lines.extend(self.ocr.recognize(self.preprocessor.process(image), page=page_no))
        return ExtractionResult(filename=filename, fields=extract_fields(lines, titles))
