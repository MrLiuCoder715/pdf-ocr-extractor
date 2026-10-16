from io import BytesIO

from openpyxl import load_workbook

from pdf_ocr_extractor.excel_writer import SHEET_TITLE, write_workbook
from pdf_ocr_extractor.models import ExtractionResult

RESULTS = [
    ExtractionResult("a.pdf", {"工程編號": "A1", "日期": "2026/10/16"}),
    ExtractionResult("b.pdf", {"工程編號": "B2", "日期": ""}),
]


def load(data: bytes):
    return load_workbook(BytesIO(data))[SHEET_TITLE]


def test_header_and_rows():
    ws = load(write_workbook(RESULTS, ["工程編號", "日期"]))
    rows = [[c if c is not None else "" for c in r] for r in ws.iter_rows(values_only=True)]
    assert rows == [
        ["檔名", "工程編號", "日期"],
        ["a.pdf", "A1", "2026/10/16"],
        ["b.pdf", "B2", ""],
    ]


def test_column_order_follows_titles():
    ws = load(write_workbook(RESULTS, ["日期", "工程編號"]))
    assert [c.value for c in ws[1]] == ["檔名", "日期", "工程編號"]
    assert [c.value for c in ws[2]] == ["a.pdf", "2026/10/16", "A1"]


def test_header_bold_and_frozen():
    ws = load(write_workbook(RESULTS, ["工程編號"]))
    assert all(c.font.bold for c in ws[1])
    assert ws.freeze_panes == "A2"


def test_values_kept_as_text():
    ws = load(write_workbook([ExtractionResult("c.pdf", {"編號": "00123"})], ["編號"]))
    cell = ws["B2"]
    assert cell.value == "00123"
    assert cell.data_type == "s"


def test_missing_field_is_blank():
    ws = load(write_workbook([ExtractionResult("d.pdf", {})], ["編號"]))
    assert ws["B2"].value in (None, "")


def test_formula_like_values_stored_as_text():
    ws = load(write_workbook([ExtractionResult("=evil.pdf", {"編號": "=1+1"})], ["編號"]))
    assert ws["A2"].data_type == "s" and ws["A2"].value == "=evil.pdf"
    assert ws["B2"].data_type == "s" and ws["B2"].value == "=1+1"
