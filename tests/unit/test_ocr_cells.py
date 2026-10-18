import numpy as np

from pdf_ocr_extractor.models import Rect
from pdf_ocr_extractor.ocr_engine import TesseractOcrEngine

EMPTY_DATA = {k: [] for k in ["text", "conf", "block_num", "par_num", "line_num", "left", "top", "width", "height"]}


class FixedDetector:
    def __init__(self, cells, mask=None):
        self.cells, self.mask = cells, mask

    def detect(self, binary):
        mask = self.mask if self.mask is not None else np.zeros_like(binary)
        return self.cells, mask


def page_with_ink(*rects):
    img = np.full((100, 200), 255, dtype=np.uint8)
    for x, y, w, h in rects:
        img[y : y + h, x : x + w] = 0
    return img


def make_engine(cells, cell_texts, seen_pages=None, string_calls=None, mask=None):
    texts = iter(cell_texts)

    def image_to_data(image, lang, output_type):
        if seen_pages is not None:
            seen_pages.append(image.copy())
        return EMPTY_DATA

    def image_to_string(image, lang, config):
        if string_calls is not None:
            string_calls.append((image.shape, lang, config))
        return next(texts)

    return TesseractOcrEngine(
        lang="chi_tra",
        image_to_data=image_to_data,
        image_to_string=image_to_string,
        detector=FixedDetector(cells, mask),
    )


def test_cell_text_becomes_table_word_with_cell_box():
    img = page_with_ink((20, 15, 10, 5))
    lines = make_engine([Rect(10, 10, 50, 20)], ["王小明\n"]).recognize(img, page=2)
    assert len(lines) == 1 and lines[0].page == 2
    word = lines[0].words[0]
    assert (word.text, word.left, word.top, word.width, word.height, word.in_table) == ("王小明", 10, 10, 50, 20, True)


def test_blank_cells_are_not_ocred():
    calls = []
    img = page_with_ink((20, 15, 10, 5))
    lines = make_engine([Rect(10, 10, 50, 20), Rect(100, 10, 50, 20)], ["1"], string_calls=calls).recognize(img, 1)
    assert len(calls) == 1
    assert [w.text for w in lines[0].words] == ["1"]


def test_cell_ocr_uses_tight_crop_single_line_mode_and_language():
    calls = []
    img = page_with_ink((20, 15, 10, 5))
    make_engine([Rect(10, 10, 50, 40)], ["x"], string_calls=calls).recognize(img, 1)
    (shape, lang, config) = calls[0]
    assert lang == "chi_tra" and "--psm 7" in config
    assert shape == (5 + 40, 10 + 40)               # 5x10 ink area plus 20px white padding per side


def test_cells_in_same_row_merge_into_one_line():
    img = page_with_ink((15, 15, 5, 5), (75, 15, 5, 5))
    lines = make_engine([Rect(60, 10, 50, 20), Rect(10, 10, 50, 20)], ["王小明", "2"]).recognize(img, 1)
    assert [[w.text for w in ln.words] for ln in lines] == [["2", "王小明"]]


def test_table_area_and_lines_blanked_before_page_ocr():
    seen = []
    img = page_with_ink((20, 15, 10, 5), (150, 80, 10, 5))
    mask = np.zeros_like(img)
    mask[80:85, 150:160] = 255
    make_engine([Rect(10, 10, 50, 20)], ["x"], seen_pages=seen, mask=mask).recognize(img, 1)
    page = seen[0]
    assert (page[10:30, 10:60] == 255).all()        # cell area blanked
    assert (page[80:85, 150:160] == 255).all()      # ruling line blanked
    assert (img[15:20, 20:30] == 0).all()           # original image untouched
