"""Browser E2E tests. Requires the app running (docker compose up) — see README.

Run: uv run pytest -m e2e
"""

import os
from io import BytesIO

import pytest
from openpyxl import load_workbook
from playwright.sync_api import Page, expect

from tests.conftest import make_pdf

pytestmark = pytest.mark.e2e

BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:8000")
OCR_TIMEOUT_MS = 120_000


@pytest.fixture
def ui(page: Page) -> Page:
    page.goto(BASE_URL)
    page.evaluate("localStorage.clear()")
    page.reload()
    return page


def title_items(page: Page):
    return page.get_by_role("list", name="標題清單").get_by_role("listitem")


def add_title(page: Page, title: str) -> None:
    page.get_by_label("新標題").fill(title)
    page.get_by_role("button", name="新增").click()


def test_default_title_present(ui: Page):
    expect(title_items(ui)).to_have_count(1)
    expect(title_items(ui).first).to_contain_text("工程編號")


def test_add_delete_and_persist_titles(ui: Page):
    add_title(ui, "日期")
    expect(title_items(ui)).to_have_count(2)

    add_title(ui, "工程編號")
    expect(ui.get_by_role("status")).to_contain_text("已存在")
    expect(title_items(ui)).to_have_count(2)

    ui.reload()
    expect(title_items(ui)).to_have_count(2)
    expect(title_items(ui).nth(1)).to_contain_text("日期")

    ui.get_by_role("button", name="刪除 日期").click()
    expect(title_items(ui)).to_have_count(1)


def test_extract_without_file_shows_error(ui: Page):
    ui.get_by_role("button", name="開始擷取").click()
    expect(ui.get_by_role("status")).to_contain_text("請先選擇 PDF")


def test_upload_extract_and_download_excel(ui: Page, tmp_path):
    pdf_path = tmp_path / "工程文件.pdf"
    pdf_path.write_bytes(make_pdf([["工程編號：nglc5zxxxd", "日期：2026/10/16"]]))
    add_title(ui, "日期")

    ui.get_by_label("選擇 PDF").set_input_files(pdf_path)
    ui.get_by_role("button", name="開始擷取").click()

    table = ui.locator("#result-table")
    expect(table).to_contain_text("nglc5zxxxd", timeout=OCR_TIMEOUT_MS)
    expect(table).to_contain_text("工程文件.pdf")
    expect(table).to_contain_text("2026/10/16")

    with ui.expect_download() as info:
        ui.get_by_role("button", name="下載 Excel").click()
    target = tmp_path / info.value.suggested_filename
    info.value.save_as(target)

    ws = load_workbook(BytesIO(target.read_bytes())).active
    assert [c.value for c in ws[1]] == ["檔名", "工程編號", "日期"]
    assert [c.value for c in ws[2]] == ["工程文件.pdf", "nglc5zxxxd", "2026/10/16"]
