"""Flask web UI and JSON API."""

from collections.abc import Sequence
from io import BytesIO
from typing import Any, Protocol

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge

from pdf_ocr_extractor.config import Settings
from pdf_ocr_extractor.excel_writer import write_workbook
from pdf_ocr_extractor.models import ExtractionResult
from pdf_ocr_extractor.ocr_engine import TesseractOcrEngine
from pdf_ocr_extractor.pdf_renderer import InvalidPdfError, PyMuPdfRenderer
from pdf_ocr_extractor.preprocess import OpenCvPreprocessor
from pdf_ocr_extractor.service import ExtractionService
from pdf_ocr_extractor.tabulate import build_table

XLSX_MIMETYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
EXPORT_FILENAME = "ocr_results.xlsx"


class Extractor(Protocol):
    def extract(
        self, pdf_bytes: bytes, filename: str, titles: Sequence[str], column_titles: Sequence[str] = ()
    ) -> ExtractionResult: ...


def build_service(settings: Settings) -> ExtractionService:
    return ExtractionService(
        renderer=PyMuPdfRenderer(dpi=settings.ocr_dpi, max_pages=settings.max_pages),
        preprocessor=OpenCvPreprocessor(),
        ocr=TesseractOcrEngine(lang=settings.ocr_lang, tesseract_cmd=settings.tesseract_cmd),
    )


def clean_titles(raw: Sequence[str]) -> list[str]:
    seen: list[str] = []
    for title in (t.strip() for t in raw):
        if title and title not in seen:
            seen.append(title)
    return seen


def _basename(filename: str) -> str:
    return filename.replace("\\", "/").rsplit("/", 1)[-1]


def _error(message: str, status: int = 400):
    return jsonify(error=message), status


def _is_str_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def _parse_result(item: Any) -> ExtractionResult | None:
    if not isinstance(item, dict):
        return None
    filename, fields, rows = item.get("filename"), item.get("fields"), item.get("rows", [])
    if not isinstance(filename, str) or not isinstance(fields, dict) or not isinstance(rows, list):
        return None
    if not all(isinstance(r, dict) for r in rows):
        return None
    return ExtractionResult(
        filename,
        {str(k): str(v) for k, v in fields.items()},
        [{str(k): str(v) for k, v in r.items()} for r in rows],
    )


def _parse_export_payload(payload: Any) -> tuple[list[str], list[str], list[ExtractionResult]] | None:
    if not isinstance(payload, dict):
        return None
    titles, results = payload.get("titles"), payload.get("results")
    column_titles = payload.get("column_titles", [])
    if not _is_str_list(titles) or not _is_str_list(column_titles) or not isinstance(results, list):
        return None
    parsed = [_parse_result(item) for item in results]
    if any(r is None for r in parsed):
        return None
    return titles, column_titles, parsed


def _table_json(results: Sequence[ExtractionResult], titles: Sequence[str], column_titles: Sequence[str]):
    header, rows = build_table(results, titles, column_titles)
    return {"header": header, "rows": rows}


def create_app(service: Extractor | None = None, settings: Settings | None = None) -> Flask:
    settings = settings or Settings.from_env()
    extractor = service or build_service(settings)
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = settings.max_upload_mb * 1024 * 1024

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_exc):
        return _error(f"上傳檔案超過 {settings.max_upload_mb} MB 上限", 413)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/extract")
    def extract():
        files = [f for f in request.files.getlist("files") if f and f.filename]
        titles = clean_titles(request.form.getlist("titles"))
        requested = set(clean_titles(request.form.getlist("column_titles")))
        column_titles = [t for t in titles if t in requested]
        if not files:
            return _error("請選擇至少一個 PDF 檔案")
        if not titles:
            return _error("請至少新增一個擷取標題")
        uploads: list[tuple[str, bytes]] = []
        for f in files:
            name = _basename(f.filename)
            data = f.read()
            if not name.lower().endswith(".pdf") or not data.startswith(b"%PDF-"):
                return _error(f"{name} 不是 PDF 檔案")
            uploads.append((name, data))
        results = []
        for name, data in uploads:
            try:
                results.append(extractor.extract(data, name, titles, column_titles))
            except InvalidPdfError:
                return _error(f"{name} 無法讀取，可能已損毀")
        return jsonify(
            titles=titles,
            column_titles=column_titles,
            results=[{"filename": r.filename, "fields": r.fields, "rows": r.rows} for r in results],
            table=_table_json(results, titles, column_titles),
        )

    @app.post("/api/export")
    def export():
        parsed = _parse_export_payload(request.get_json(silent=True))
        if parsed is None:
            return _error("匯出資料格式錯誤")
        titles, column_titles, results = parsed
        header, rows = build_table(results, titles, column_titles)
        return send_file(
            BytesIO(write_workbook(header, rows)),
            mimetype=XLSX_MIMETYPE,
            as_attachment=True,
            download_name=EXPORT_FILENAME,
        )

    return app
