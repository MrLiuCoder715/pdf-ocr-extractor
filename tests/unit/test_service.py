import numpy as np

from pdf_ocr_extractor.models import ExtractionResult, OcrLine, OcrWord
from pdf_ocr_extractor.service import ExtractionService


class FakeRenderer:
    def __init__(self, pages: int) -> None:
        self.pages = pages

    def render(self, pdf_bytes):
        return [np.full((5, 5, 3), i, dtype=np.uint8) for i in range(self.pages)]


class IdentityPreprocessor:
    def __init__(self):
        self.calls = 0

    def process(self, image):
        self.calls += 1
        return image


class ScriptedOcr:
    """Return pre-scripted text lines per page number."""

    def __init__(self, by_page: dict[int, list[str]]) -> None:
        self.by_page = by_page

    def recognize(self, image, page):
        return [
            OcrLine(page=page, words=[OcrWord(t, 0, 0, 10, 10, 90.0)]) for t in self.by_page.get(page, [])
        ]


def test_service_runs_full_pipeline_across_pages():
    pre = IdentityPreprocessor()
    service = ExtractionService(
        renderer=FakeRenderer(pages=2),
        preprocessor=pre,
        ocr=ScriptedOcr({1: ["無關文字"], 2: ["工程編號：nglc5zxxxd"]}),
    )
    result = service.extract(b"%PDF-", "a.pdf", ["工程編號", "日期"])
    assert result == ExtractionResult(filename="a.pdf", fields={"工程編號": "nglc5zxxxd", "日期": ""})
    assert pre.calls == 2


def test_page_numbers_start_at_one():
    seen = []

    class RecordingOcr:
        def recognize(self, image, page):
            seen.append(page)
            return []

    ExtractionService(FakeRenderer(3), IdentityPreprocessor(), RecordingOcr()).extract(b"", "x.pdf", ["t"])
    assert seen == [1, 2, 3]


def test_service_extracts_table_rows_for_column_titles():
    def words(*cells):
        return [OcrWord(t, x, 0, 100, 50, 0.0, in_table=True) for t, x in cells]

    class TableOcr:
        def recognize(self, image, page):
            if page == 1:
                return [OcrLine(1, [OcrWord("承商名稱", 0, 0, 80, 20, 90.0), OcrWord("樺佑", 100, 0, 40, 20, 90.0)]),
                        OcrLine(1, words(("姓名", 500))), OcrLine(1, words(("王小明", 500)))]
            return [OcrLine(2, words(("陳大華", 500)))]

    service = ExtractionService(FakeRenderer(pages=2), IdentityPreprocessor(), TableOcr())
    result = service.extract(b"", "a.pdf", ["承商名稱", "姓名"], column_titles=["姓名"])
    assert result.fields == {"承商名稱": "樺佑"}
    assert result.rows == [{"姓名": "王小明"}, {"姓名": "陳大華"}]


def test_service_without_column_titles_has_no_rows():
    service = ExtractionService(FakeRenderer(1), IdentityPreprocessor(), ScriptedOcr({1: ["工程編號：A1"]}))
    assert service.extract(b"", "a.pdf", ["工程編號"]).rows == []
