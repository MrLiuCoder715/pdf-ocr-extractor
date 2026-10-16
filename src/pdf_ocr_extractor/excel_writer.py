"""Write extraction results to an .xlsx workbook."""

from collections.abc import Sequence
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font

from pdf_ocr_extractor.models import ExtractionResult

SHEET_TITLE = "擷取結果"
FILENAME_HEADER = "檔名"


def _append_text_row(ws, values: Sequence[str]) -> None:
    ws.append(list(values))
    for cell in ws[ws.max_row]:
        if cell.value not in (None, ""):
            # Force string type so OCR text like "=..." is never evaluated as a formula.
            cell.data_type = "s"


def write_workbook(results: Sequence[ExtractionResult], titles: Sequence[str]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_TITLE
    _append_text_row(ws, [FILENAME_HEADER, *titles])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    ws.freeze_panes = "A2"
    for result in results:
        _append_text_row(ws, [result.filename, *(result.fields.get(t, "") for t in titles)])
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
