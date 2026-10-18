from pdf_ocr_extractor.models import ExtractionResult
from pdf_ocr_extractor.tabulate import build_table


def test_one_row_per_pdf_without_column_titles():
    results = [ExtractionResult("a.pdf", {"工程編號": "A1"}), ExtractionResult("b.pdf", {})]
    header, rows = build_table(results, ["工程編號"], [])
    assert header == ["檔名", "工程編號"]
    assert rows == [["a.pdf", "A1"], ["b.pdf", ""]]


def test_one_row_per_table_row_with_fields_repeated():
    result = ExtractionResult(
        "a.pdf", {"承商名稱": "樺佑"}, rows=[{"姓名": "王小明"}, {"姓名": "陳大華"}]
    )
    header, rows = build_table([result], ["承商名稱", "姓名"], ["姓名"])
    assert header == ["檔名", "承商名稱", "姓名"]
    assert rows == [["a.pdf", "樺佑", "王小明"], ["a.pdf", "樺佑", "陳大華"]]


def test_column_order_follows_titles():
    result = ExtractionResult("a.pdf", {"承商名稱": "樺佑"}, rows=[{"項次": "1", "姓名": "王小明"}])
    _, rows = build_table([result], ["姓名", "承商名稱", "項次"], ["項次", "姓名"])
    assert rows == [["a.pdf", "王小明", "樺佑", "1"]]


def test_pdf_without_table_rows_still_gets_one_row():
    result = ExtractionResult("b.pdf", {"承商名稱": "樺佑"}, rows=[])
    _, rows = build_table([result], ["承商名稱", "姓名"], ["姓名"])
    assert rows == [["b.pdf", "樺佑", ""]]
