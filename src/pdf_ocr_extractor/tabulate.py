"""Expand extraction results into the rows shown in the preview and written to Excel."""

from collections.abc import Collection, Sequence

from pdf_ocr_extractor.models import ExtractionResult

FILENAME_HEADER = "檔名"


def build_table(
    results: Sequence[ExtractionResult],
    titles: Sequence[str],
    column_titles: Collection[str],
) -> tuple[list[str], list[list[str]]]:
    """One row per PDF, or — when table columns exist — one row per table row of each PDF."""
    header = [FILENAME_HEADER, *titles]
    rows: list[list[str]] = []
    for result in results:
        table_rows = (result.rows or [{}]) if column_titles else [{}]
        for table_row in table_rows:
            rows.append(
                [
                    result.filename,
                    *(
                        table_row.get(t, "") if t in column_titles else result.fields.get(t, "")
                        for t in titles
                    ),
                ]
            )
    return header, rows
