"""
URL scraper parser.
Downloads a web page, strips HTML, returns clean text as a ParsedDocument.
Uses httpx for async-friendly HTTP and BeautifulSoup for HTML parsing.
"""
from dataclasses import dataclass, field


@dataclass
class ParsedDocument:
    pages: list
    page_count: int = 1

    @property
    def full_text(self) -> str:
        return "\n\n".join(p["text"] for p in self.pages if p["text"].strip())


def parse(file_bytes: bytes) -> ParsedDocument:
    """
    Called by the ingestion pipeline with the raw downloaded bytes.
    For URL scrapes the pipeline passes the HTML bytes directly.
    """
    return _extract_text(file_bytes)


def scrape_url(url: str) -> ParsedDocument:
    """
    Synchronous entry point — downloads + parses a URL.
    Called by the pipeline when source == 'url_scrape'.
    """
    import httpx

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; DocMind/1.0; +https://docmind.ai/bot)"
        )
    }
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()

    return _extract_text(response.content)


def _extract_text(html_bytes: bytes) -> ParsedDocument:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_bytes, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "noscript", "iframe", "form"]):
        tag.decompose()

    # Prefer <article> or <main> if available
    main = soup.find("article") or soup.find("main") or soup.find("body") or soup

    # Extract text with newlines preserved
    lines: list[str] = []
    for elem in main.descendants:  # type: ignore[union-attr]
        if hasattr(elem, "name"):
            if elem.name in ("p", "h1", "h2", "h3", "h4", "h5", "h6",
                             "li", "td", "th", "blockquote", "pre"):
                text = elem.get_text(separator=" ", strip=True)
                if text:
                    lines.append(text)

    text = "\n\n".join(lines) if lines else main.get_text(separator="\n", strip=True)  # type: ignore[union-attr]

    return ParsedDocument(pages=[{"page_number": 1, "text": text.strip()}])
