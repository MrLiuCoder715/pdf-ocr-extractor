from io import BytesIO

import pytest
from openpyxl import load_workbook

from pdf_ocr_extractor.config import Settings
from pdf_ocr_extractor.excel_writer import SHEET_TITLE
from pdf_ocr_extractor.models import ExtractionResult
from pdf_ocr_extractor.pdf_renderer import InvalidPdfError
from pdf_ocr_extractor.web import create_app

PDF = b"%PDF-1.7 fake body"


class FakeService:
    def __init__(self):
        self.calls = []

    def extract(self, pdf_bytes, filename, titles):
        self.calls.append((filename, list(titles)))
        if b"broken" in pdf_bytes:
            raise InvalidPdfError("bad")
        return ExtractionResult(filename, {t: f"{t}-value" for t in titles})


@pytest.fixture
def service():
    return FakeService()


@pytest.fixture
def client(service):
    app = create_app(service=service, settings=Settings(max_upload_mb=1))
    app.testing = True
    return app.test_client()


def post_extract(client, files, titles):
    data = {"titles": titles, "files": [(BytesIO(body), name) for name, body in files]}
    return client.post("/api/extract", data=data, content_type="multipart/form-data")


def test_index_serves_ui(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "PDF" in resp.get_data(as_text=True)


def test_extract_success(client, service):
    resp = post_extract(client, [("a.pdf", PDF), ("b.PDF", PDF)], ["工程編號", "日期"])
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["titles"] == ["工程編號", "日期"]
    assert [r["filename"] for r in body["results"]] == ["a.pdf", "b.PDF"]
    assert body["results"][0]["fields"] == {"工程編號": "工程編號-value", "日期": "日期-value"}


def test_extract_cleans_titles(client, service):
    resp = post_extract(client, [("a.pdf", PDF)], [" 工程編號 ", "", "工程編號", "日期"])
    assert resp.get_json()["titles"] == ["工程編號", "日期"]
    assert service.calls == [("a.pdf", ["工程編號", "日期"])]


def test_extract_keeps_only_basename(client):
    resp = post_extract(client, [("scan/工程.pdf", PDF)], ["工程編號"])
    assert resp.get_json()["results"][0]["filename"] == "工程.pdf"


def test_extract_requires_files(client):
    resp = client.post("/api/extract", data={"titles": ["工程編號"]}, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_extract_requires_titles(client):
    resp = post_extract(client, [("a.pdf", PDF)], ["  "])
    assert resp.status_code == 400
    assert "error" in resp.get_json()


@pytest.mark.parametrize("name,body", [("note.txt", PDF), ("fake.pdf", b"hello world")])
def test_extract_rejects_non_pdf(client, service, name, body):
    resp = post_extract(client, [(name, body)], ["工程編號"])
    assert resp.status_code == 400
    assert name in resp.get_json()["error"]
    assert service.calls == []


def test_extract_reports_unreadable_pdf(client):
    resp = post_extract(client, [("x.pdf", PDF + b"broken")], ["工程編號"])
    assert resp.status_code == 400
    assert "x.pdf" in resp.get_json()["error"]


def test_extract_rejects_oversized_upload(client):
    big = PDF + b"0" * (1024 * 1024 + 10)
    resp = post_extract(client, [("big.pdf", big)], ["工程編號"])
    assert resp.status_code == 413
    assert "error" in resp.get_json()


def test_export_returns_xlsx(client):
    payload = {
        "titles": ["工程編號"],
        "results": [{"filename": "a.pdf", "fields": {"工程編號": "nglc5zxxxd"}}],
    }
    resp = client.post("/api/export", json=payload)
    assert resp.status_code == 200
    assert resp.mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "attachment" in resp.headers["Content-Disposition"]
    ws = load_workbook(BytesIO(resp.data))[SHEET_TITLE]
    assert [c.value for c in ws[2]] == ["a.pdf", "nglc5zxxxd"]


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {"titles": "工程編號", "results": []},
        {"titles": ["工程編號"], "results": [{"filename": 1, "fields": {}}]},
        {"titles": ["工程編號"], "results": [{"filename": "a.pdf", "fields": []}]},
    ],
)
def test_export_rejects_bad_payload(client, payload):
    resp = client.post("/api/export", data="oops", content_type="application/json") if payload is None \
        else client.post("/api/export", json=payload)
    assert resp.status_code == 400
    assert "error" in resp.get_json()
