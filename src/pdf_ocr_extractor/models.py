"""Data models shared across the OCR and extraction layers."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int


@dataclass(frozen=True)
class OcrWord:
    text: str
    left: int
    top: int
    width: int
    height: int
    conf: float
    in_table: bool = False


@dataclass(frozen=True)
class OcrLine:
    page: int
    words: list[OcrWord] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)


@dataclass(frozen=True)
class ExtractionResult:
    filename: str
    fields: dict[str, str]
    rows: list[dict[str, str]] = field(default_factory=list)
