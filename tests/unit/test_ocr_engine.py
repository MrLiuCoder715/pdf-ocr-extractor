import numpy as np

from pdf_ocr_extractor.ocr_engine import TesseractOcrEngine


def fake_data(rows):
    """rows: (text, conf, block, par, line, left, top, width, height)"""
    keys = ["text", "conf", "block_num", "par_num", "line_num", "left", "top", "width", "height"]
    return {k: [r[i] for r in rows] for i, k in enumerate(keys)}


def engine_returning(rows, calls=None):
    def image_to_data(image, lang, output_type):
        if calls is not None:
            calls.append(lang)
        return fake_data(rows)

    return TesseractOcrEngine(lang="chi_tra+eng", image_to_data=image_to_data)


IMG = np.zeros((10, 10), dtype=np.uint8)


def texts(lines):
    return [[w.text for w in ln.words] for ln in lines]


def test_groups_words_of_same_line_left_to_right():
    rows = [
        ("nglc5zxxxd", 90, 1, 1, 1, 200, 10, 100, 20),
        ("工程編號：", 91, 1, 1, 1, 10, 10, 120, 20),
    ]
    lines = engine_returning(rows).recognize(IMG, page=3)
    assert texts(lines) == [["工程編號：", "nglc5zxxxd"]]
    assert lines[0].page == 3


def test_merges_lines_from_different_blocks_on_same_row():
    rows = [
        ("工程編號", 90, 1, 1, 1, 10, 100, 120, 30),
        ("nglc5zxxxd", 90, 2, 1, 1, 400, 105, 150, 28),
    ]
    assert texts(engine_returning(rows).recognize(IMG, page=1)) == [["工程編號", "nglc5zxxxd"]]


def test_rows_sorted_top_to_bottom_and_kept_separate():
    rows = [
        ("second", 90, 2, 1, 1, 10, 200, 80, 20),
        ("first", 90, 1, 1, 1, 10, 100, 80, 20),
    ]
    assert texts(engine_returning(rows).recognize(IMG, page=1)) == [["first"], ["second"]]


def test_skips_blank_and_negative_conf_entries():
    rows = [
        ("", -1, 1, 0, 0, 0, 0, 500, 500),
        ("   ", 95, 1, 1, 1, 0, 10, 5, 20),
        ("ghost", -1, 1, 1, 1, 50, 10, 30, 20),
        ("ok", "88.5", 1, 1, 1, 90, 10, 30, 20),
    ]
    lines = engine_returning(rows).recognize(IMG, page=1)
    assert texts(lines) == [["ok"]]
    assert lines[0].words[0].conf == 88.5


def test_passes_configured_language():
    calls = []
    engine_returning([], calls).recognize(IMG, page=1)
    assert calls == ["chi_tra+eng"]
