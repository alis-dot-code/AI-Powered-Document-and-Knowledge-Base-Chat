"""Plain text parser."""
from dataclasses import dataclass, field


@dataclass
class ParsedDocument:
    pages: list
    page_count: int = 1

    @property
    def full_text(self) -> str:
        return "\n\n".join(p["text"] for p in self.pages if p["text"].strip())


def parse(file_bytes: bytes) -> ParsedDocument:
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            text = file_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = file_bytes.decode("utf-8", errors="replace")

    return ParsedDocument(pages=[{"page_number": 1, "text": text.strip()}])
