"""Run the development server: python -m pdf_ocr_extractor"""

from pdf_ocr_extractor.config import Settings
from pdf_ocr_extractor.web import create_app

if __name__ == "__main__":
    settings = Settings.from_env()
    create_app(settings=settings).run(host="127.0.0.1", port=settings.port)
