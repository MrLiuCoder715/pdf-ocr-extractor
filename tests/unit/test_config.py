from pdf_ocr_extractor.config import Settings


def test_defaults_when_env_empty():
    s = Settings.from_env({})
    assert s.ocr_lang == "chi_tra"
    assert s.ocr_dpi == 300
    assert s.max_pages == 20
    assert s.max_upload_mb == 50
    assert s.tesseract_cmd is None
    assert s.port == 8000


def test_values_read_from_env():
    s = Settings.from_env(
        {
            "OCR_LANG": "eng",
            "OCR_DPI": "200",
            "MAX_PAGES": "5",
            "MAX_UPLOAD_MB": "10",
            "TESSERACT_CMD": "/usr/bin/tesseract",
            "PORT": "9000",
        }
    )
    assert (s.ocr_lang, s.ocr_dpi, s.max_pages, s.max_upload_mb) == ("eng", 200, 5, 10)
    assert s.tesseract_cmd == "/usr/bin/tesseract"
    assert s.port == 9000
