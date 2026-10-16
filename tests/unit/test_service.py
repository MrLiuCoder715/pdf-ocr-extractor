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
