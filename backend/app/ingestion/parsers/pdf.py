"""PDF parser using pdfplumber (text-based PDFs) with pymupdf fallback."""
from dataclasses import dataclass, field


@dataclass
class ParsedPage:
    page_number: int
    text: str


@dataclass
class ParsedDocument:
    pages: list[ParsedPage] = field(default_factory=list)
    page_count: int = 0

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text.strip())


def parse(file_bytes: bytes) -> ParsedDocument:
    import io
    import pdfplumber

    result = ParsedDocument()
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        result.page_count = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            result.pages.append(ParsedPage(page_number=i, text=text.strip()))

    # Fallback to pymupdf if pdfplumber extracted nothing
    if not result.full_text.strip():
        import fitz  # pymupdf

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        result.pages = []
        result.page_count = doc.page_count
        for i, page in enumerate(doc, start=1):
            text = page.get_text()
            result.pages.append(ParsedPage(page_number=i, text=text.strip()))
        doc.close()

    return result
