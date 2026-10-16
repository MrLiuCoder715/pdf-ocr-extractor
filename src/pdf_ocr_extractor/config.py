"""Application settings read from environment variables."""

import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    ocr_lang: str = "chi_tra+eng"
    ocr_dpi: int = 300
    max_pages: int = 20
    max_upload_mb: int = 50
    tesseract_cmd: str | None = None
    port: int = 8000

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        env = os.environ if env is None else env
        return cls(
            ocr_lang=env.get("OCR_LANG") or cls.ocr_lang,
            ocr_dpi=int(env.get("OCR_DPI") or cls.ocr_dpi),
            max_pages=int(env.get("MAX_PAGES") or cls.max_pages),
            max_upload_mb=int(env.get("MAX_UPLOAD_MB") or cls.max_upload_mb),
            tesseract_cmd=env.get("TESSERACT_CMD") or None,
            port=int(env.get("PORT") or cls.port),
        )
