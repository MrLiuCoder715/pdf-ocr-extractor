"""Orchestrates render -> preprocess -> OCR -> field extraction for one PDF."""

from collections.abc import Sequence

from pdf_ocr_extractor.field_extractor import extract_fields, extract_table
from pdf_ocr_extractor.models import ExtractionResult, OcrLine
from pdf_ocr_extractor.ocr_engine import OcrEngine
from pdf_ocr_extractor.pdf_renderer import PdfRenderer
from pdf_ocr_extractor.preprocess import ImagePreprocessor


class ExtractionService:
    def __init__(self, renderer: PdfRenderer, preprocessor: ImagePreprocessor, ocr: OcrEngine) -> None:
        self.renderer = renderer
        self.preprocessor = preprocessor
        self.ocr = ocr

    def extract(
        self,
        pdf_bytes: bytes,
        filename: str,
        titles: Sequence[str],
        column_titles: Sequence[str] = (),
    ) -> ExtractionResult:
        lines: list[OcrLine] = []
        for page_no, image in enumerate(self.renderer.render(pdf_bytes), start=1):
            lines.extend(self.ocr.recognize(self.preprocessor.process(image), page=page_no))
        # All titles feed extract_fields so column headers also stop a field value.
        fields = {t: v for t, v in extract_fields(lines, titles).items() if t not in column_titles}
        rows = extract_table(lines, [t for t in titles if t in column_titles])
        return ExtractionResult(filename=filename, fields=fields, rows=rows)
