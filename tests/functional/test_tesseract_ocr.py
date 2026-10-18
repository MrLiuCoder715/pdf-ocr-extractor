import pytest

from pdf_ocr_extractor.ocr_engine import TesseractOcrEngine
from pdf_ocr_extractor.pdf_renderer import PyMuPdfRenderer
from pdf_ocr_extractor.preprocess import OpenCvPreprocessor

pytestmark = pytest.mark.tesseract


def test_real_tesseract_reads_scanned_pdf(pdf_factory):
    pdf = pdf_factory([["工程編號：nglc5zxxxd"]])
    image = OpenCvPreprocessor().process(PyMuPdfRenderer(dpi=300, max_pages=5).render(pdf)[0])
    lines = TesseractOcrEngine(lang="chi_tra").recognize(image, page=1)
    assert "nglc5zxxxd" in " ".join(line.text for line in lines)
