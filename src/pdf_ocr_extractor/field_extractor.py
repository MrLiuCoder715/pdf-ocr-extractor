"""Locate titles in OCR lines and extract the text that follows them."""

from collections.abc import Sequence

from pdf_ocr_extractor.models import OcrLine, OcrWord

# Separators plus punctuation Tesseract tends to hallucinate between a label and its value.
SEPARATORS = ":：-=－＝。、.,，“”‘’\"' \t"
COLUMN_OVERLAP = 0.5


def _compact(text: str) -> str:
    return "".join(text.split())


def _is_ascii_alnum(char: str) -> bool:
    return char.isascii() and char.isalnum()


def join_tokens(tokens: Sequence[str]) -> str:
    """Join tokens, spacing only where an ASCII alphanumeric end meets an ASCII alphanumeric start."""
    out = ""
    for token in tokens:
        if out and token and _is_ascii_alnum(out[-1]) and _is_ascii_alnum(token[0]):
            out += " "
        out += token
    return out


def _strip_leading_separators(tokens: list[str]) -> list[str]:
    while tokens:
        first = tokens[0].lstrip(SEPARATORS)
        if first:
            return [first, *tokens[1:]]
        tokens = tokens[1:]
    return tokens


def _split_at(tokens: list[str], pos: int) -> tuple[list[str], list[str]]:
    """Split tokens at character offset `pos` of their concatenation."""
    consumed = 0
    for i, token in enumerate(tokens):
        if consumed + len(token) >= pos:
            cut = pos - consumed
            head = [*tokens[:i], token[:cut]] if cut else tokens[:i]
            tail = [token[cut:], *tokens[i + 1 :]] if cut < len(token) else tokens[i + 1 :]
            return head, tail
        consumed += len(token)
    return tokens, []


def _tokens_after_title(line: OcrLine, title: str, others: Sequence[str]) -> list[str] | None:
    """Return the tokens following `title` up to the next other title, or None if absent."""
    tokens = [_compact(w.text) for w in line.words]
    start = "".join(tokens).find(title)
    if start < 0:
        return None
    _, after = _split_at(tokens, start + len(title))
    rest = "".join(after)
    cuts = [p for p in (rest.find(o) for o in others) if p >= 0]
    if cuts:
        after, _ = _split_at(after, min(cuts))
    return _strip_leading_separators(after)


def _extract_one(lines: Sequence[OcrLine], title: str, others: Sequence[str]) -> str:
    if not title:
        return ""
    for line in lines:
        tokens = _tokens_after_title(line, title, others)
        if tokens is not None:
            return join_tokens(tokens)
    return ""


def extract_fields(lines: Sequence[OcrLine], titles: Sequence[str]) -> dict[str, str]:
    """Map each title to the first value found after it (empty string when absent)."""
    compact = [_compact(t) for t in titles]
    return {
        title: _extract_one(lines, key, [o for o in compact if o and o != key])
        for title, key in zip(titles, compact)
    }


def _title_words(line: OcrLine, title: str) -> list[OcrWord]:
    """Return the words of `line` that make up `title` (ignoring whitespace), or [] if absent."""
    tokens = [_compact(w.text) for w in line.words]
    start = "".join(tokens).find(title) if title else -1
    if start < 0:
        return []
    end = start + len(title)
    spanned, offset = [], 0
    for word, token in zip(line.words, tokens):
        if offset < end and offset + len(token) > start:
            spanned.append(word)
        offset += len(token)
    return spanned


def _overlaps(word: OcrWord, x0: int, x1: int) -> bool:
    overlap = min(word.left + word.width, x1) - max(word.left, x0)
    return overlap > 0 and overlap >= COLUMN_OVERLAP * min(word.width, x1 - x0)


class _Column:
    def __init__(self, title: str, line_index: int, header: list[OcrWord]) -> None:
        self.title = title
        self.line_index = line_index
        self.x0 = min(w.left for w in header)
        self.x1 = max(w.left + w.width for w in header)
        self.table_only = all(w.in_table for w in header)

    def value(self, line: OcrLine) -> str:
        words = [
            w for w in line.words
            if _overlaps(w, self.x0, self.x1) and (w.in_table or not self.table_only)
        ]
        return join_tokens(_strip_leading_separators([_compact(w.text) for w in words]))


def _find_column(lines: Sequence[OcrLine], title: str, key: str) -> _Column | None:
    for idx, line in enumerate(lines):
        header = _title_words(line, key)
        if header:
            return _Column(title, idx, header)
    return None


def extract_table(lines: Sequence[OcrLine], column_titles: Sequence[str]) -> list[dict[str, str]]:
    """Collect, row by row, the values below each column header (continuing onto later pages)."""
    keys = {title: _compact(title) for title in column_titles}
    columns = [c for c in (_find_column(lines, t, k) for t, k in keys.items()) if c is not None]
    if not columns:
        return []
    rows: list[dict[str, str]] = []
    for idx in range(min(c.line_index for c in columns) + 1, len(lines)):
        line = lines[idx]
        if any(_title_words(line, keys[c.title]) for c in columns):
            continue  # repeated header row
        values = {c.title: c.value(line) if idx > c.line_index else "" for c in columns}
        if any(values.values()):
            rows.append({title: values.get(title, "") for title in column_titles})
    return rows
