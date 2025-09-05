"""CSV parser — converts rows to readable text blocks."""
import csv
import io
from dataclasses import dataclass


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
            text_io = io.StringIO(file_bytes.decode(enc))
            break
        except UnicodeDecodeError:
            continue
    else:
        text_io = io.StringIO(file_bytes.decode("utf-8", errors="replace"))

    reader = csv.DictReader(text_io)
    headers = reader.fieldnames or []
    rows = list(reader)

    lines: list[str] = []
    if headers:
        lines.append("Columns: " + ", ".join(headers))
        lines.append("")

    for i, row in enumerate(rows, start=1):
        parts = [f"{k}: {v}" for k, v in row.items() if v]
        lines.append(f"Row {i}: " + " | ".join(parts))

    return ParsedDocument(pages=[{"page_number": 1, "text": "\n".join(lines)}])
