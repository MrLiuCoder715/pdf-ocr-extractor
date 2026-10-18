from pdf_ocr_extractor.field_extractor import extract_table
from pdf_ocr_extractor.models import OcrLine, OcrWord

# Column x-ranges of a roster-style table: 項次 | 姓名 | 大頭照
NUM, NAME, PHOTO = (900, 250), (1160, 250), (1420, 1180)


def cell(text, col, top=0, in_table=True):
    x, w = col
    return OcrWord(text=text, left=x, top=top, width=w, height=100, conf=0.0, in_table=in_table)


def row(*words, page=1):
    return OcrLine(page=page, words=list(words))


HEADER = row(cell("項次", NUM), cell("姓 名", NAME), cell("大頭照", PHOTO))


def test_collects_every_value_below_header():
    lines = [HEADER, row(cell("1", NUM), cell("王小明", NAME)), row(cell("2", NUM), cell("陳大華", NAME))]
    assert extract_table(lines, ["姓名"]) == [{"姓名": "王小明"}, {"姓名": "陳大華"}]


def test_continues_on_following_pages_without_header():
    lines = [
        HEADER,
        row(cell("1", NUM), cell("王小明", NAME)),
        row(cell("3", NUM), cell("陳大華", NAME), page=2),
        row(cell("6", NUM), cell("林志玲", NAME), page=3),
    ]
    assert [r["姓名"] for r in extract_table(lines, ["姓名"])] == ["王小明", "陳大華", "林志玲"]


def test_multiple_columns_aligned_by_row():
    lines = [HEADER, row(cell("1", NUM)), row(cell("2", NUM), cell("王小明", NAME))]
    assert extract_table(lines, ["項次", "姓名"]) == [
        {"項次": "1", "姓名": ""},
        {"項次": "2", "姓名": "王小明"},
    ]


def test_skips_empty_rows_and_text_outside_the_table():
    footer = OcrWord("第1頁", left=1170, top=0, width=100, height=30, conf=90.0, in_table=False)
    lines = [HEADER, row(cell("1", NUM)), row(cell("2", NUM), cell("王小明", NAME)), row(footer)]
    assert extract_table(lines, ["姓名"]) == [{"姓名": "王小明"}]


def test_words_outside_column_range_ignored():
    lines = [HEADER, row(cell("2", NUM), cell("王小明", NAME), cell("圖", PHOTO))]
    assert extract_table(lines, ["姓名"]) == [{"姓名": "王小明"}]


def test_repeated_header_row_skipped():
    lines = [HEADER, row(cell("1", NUM), cell("王小明", NAME)), OcrLine(page=2, words=HEADER.words)]
    assert extract_table(lines, ["姓名"]) == [{"姓名": "王小明"}]


def test_header_split_across_words_outside_table():
    header = row(
        OcrWord("姓", 1170, 0, 40, 30, 90.0), OcrWord("名", 1260, 0, 40, 30, 90.0), OcrWord("職稱", 1600, 0, 80, 30, 90.0)
    )
    value = row(OcrWord("王小明", 1180, 0, 110, 30, 90.0))
    assert extract_table([header, value], ["姓名"]) == [{"姓名": "王小明"}]


def test_missing_header_gives_no_rows():
    assert extract_table([HEADER, row(cell("1", NUM))], ["職稱"]) == []


def test_no_column_titles_gives_no_rows():
    assert extract_table([HEADER], []) == []
