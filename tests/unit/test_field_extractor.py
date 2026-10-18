from pdf_ocr_extractor.field_extractor import extract_fields
from pdf_ocr_extractor.models import OcrLine, OcrWord


def line(*texts: str, page: int = 1) -> OcrLine:
    words = [OcrWord(text=t, left=i * 50, top=0, width=40, height=20, conf=90.0) for i, t in enumerate(texts)]
    return OcrLine(page=page, words=words)


def test_value_after_fullwidth_colon():
    assert extract_fields([line("工程編號：nglc5zxxxd")], ["工程編號"]) == {"工程編號": "nglc5zxxxd"}


def test_value_after_separate_tokens():
    assert extract_fields([line("工程編號：", "nglc5zxxxd")], ["工程編號"]) == {"工程編號": "nglc5zxxxd"}


def test_ocr_inserts_spaces_between_chinese_chars():
    lines = [line("工", "程", "編", "號", ":", "nglc5zxxxd")]
    assert extract_fields(lines, ["工程編號"]) == {"工程編號": "nglc5zxxxd"}


def test_title_spans_part_of_a_word():
    lines = [line("工程", "編號:nglc5zxxxd")]
    assert extract_fields(lines, ["工程編號"]) == {"工程編號": "nglc5zxxxd"}


def test_ascii_words_joined_with_space():
    assert extract_fields([line("工程名稱", "Phase", "2")], ["工程名稱"]) == {"工程名稱": "Phase 2"}


def test_chinese_words_joined_without_space():
    assert extract_fields([line("工程名稱", "台", "北", "站")], ["工程名稱"]) == {"工程名稱": "台北站"}


def test_leading_separators_removed():
    assert extract_fields([line("日期", "=", "-", "2026/10/16")], ["日期"]) == {"日期": "2026/10/16"}


def test_blank_value_does_not_take_next_line():
    lines = [line("工程編號"), line("契約編號", "21915A451")]
    assert extract_fields(lines, ["工程編號"]) == {"工程編號": ""}


def test_ocr_noise_punctuation_stripped():
    assert extract_fields([line("承商名稱", "。", "測試公司")], ["承商名稱"]) == {"承商名稱": "測試公司"}
    assert extract_fields([line("契約編號", "“21915A451")], ["契約編號"]) == {"契約編號": "21915A451"}
    assert extract_fields([line("契約名稱。", "115年度")], ["契約名稱"]) == {"契約名稱": "115年度"}


def test_multiple_titles():
    lines = [line("工程編號：A1"), line("日期：2026/10/16")]
    assert extract_fields(lines, ["工程編號", "日期"]) == {"工程編號": "A1", "日期": "2026/10/16"}


def test_first_match_wins():
    lines = [line("工程編號：A1"), line("工程編號：B2")]
    assert extract_fields(lines, ["工程編號"]) == {"工程編號": "A1"}


def test_missing_title_gives_empty_string():
    assert extract_fields([line("工程編號：A1")], ["承包商"]) == {"承包商": ""}


def test_title_with_spaces_matches():
    assert extract_fields([line("工程編號：A1")], [" 工程 編號 "]) == {" 工程 編號 ": "A1"}


def test_blank_title_never_matches():
    assert extract_fields([line("工程編號：A1")], ["  "]) == {"  ": ""}


def test_value_truncated_at_next_title_on_same_line():
    lines = [line("工程編號：A1", "日期：2026/10/16")]
    assert extract_fields(lines, ["工程編號", "日期"]) == {"工程編號": "A1", "日期": "2026/10/16"}


def test_value_truncated_when_next_title_inside_a_token():
    lines = [line("工程編號：A1日期：2026/10/16")]
    assert extract_fields(lines, ["工程編號", "日期"]) == {"工程編號": "A1", "日期": "2026/10/16"}


def test_ocr_split_date_joined_without_spaces():
    assert extract_fields([line("日期：", "2026/", "10/", "16")], ["日期"]) == {"日期": "2026/10/16"}


def test_space_kept_between_words_around_punctuation():
    assert extract_fields([line("名稱", "Phase", "2-A", "North")], ["名稱"]) == {"名稱": "Phase 2-A North"}
