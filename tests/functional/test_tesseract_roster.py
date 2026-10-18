"""Real Tesseract on a roster-style ruled table (runs in Docker)."""

import pytest

from pdf_ocr_extractor.config import Settings
from pdf_ocr_extractor.web import build_service
from tests.conftest import ROSTER_NAMES, make_roster_pdf

pytestmark = pytest.mark.tesseract


@pytest.fixture(scope="module")
def roster_result():
    service = build_service(Settings())
    titles = ["承商名稱", "工程編號", "契約編號", "姓名"]
    return service.extract(make_roster_pdf(), "roster.pdf", titles, column_titles=["姓名"])


def test_label_fields(roster_result):
    assert roster_result.fields == {"承商名稱": "測試公司", "工程編號": "", "契約編號": "21915A451"}


def test_every_name_in_the_table_across_pages(roster_result):
    assert [r["姓名"] for r in roster_result.rows] == ROSTER_NAMES
