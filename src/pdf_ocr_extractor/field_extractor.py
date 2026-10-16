"""Locate titles in OCR lines and extract the text that follows them."""

from collections.abc import Sequence

from pdf_ocr_extractor.models import OcrLine

SEPARATORS = ":：-=－＝ \t"


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
    for idx, line in enumerate(lines):
        tokens = _tokens_after_title(line, title, others)
        if tokens is None:
            continue
        if tokens:
            return join_tokens(tokens)
        nxt = lines[idx + 1] if idx + 1 < len(lines) else None
        if nxt is not None and nxt.page == line.page:
            return join_tokens(_strip_leading_separators([_compact(w.text) for w in nxt.words]))
        return ""
    return ""


def extract_fields(lines: Sequence[OcrLine], titles: Sequence[str]) -> dict[str, str]:
    """Map each title to the first value found after it (empty string when absent)."""
    compact = [_compact(t) for t in titles]
    return {
        title: _extract_one(lines, key, [o for o in compact if o and o != key])
        for title, key in zip(titles, compact)
    }
