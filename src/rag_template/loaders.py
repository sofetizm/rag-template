from __future__ import annotations

import io
import re
from html.parser import HTMLParser
from pathlib import Path

from .documents import Document, markdown_title

TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".rst"}
HTML_SUFFIXES = {".html", ".htm"}
SUPPORTED = TEXT_SUFFIXES | HTML_SUFFIXES | {".pdf"}


class _HTMLText(HTMLParser):
    _SKIP = {"script", "style", "nav", "footer", "header", "noscript"}
    _BLOCK = {"p", "div", "li", "br", "tr", "section", "article", "pre", "table"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.title = ""
        self._skip = 0
        self._tag = ""

    def handle_starttag(self, tag, attrs):
        self._tag = tag
        if tag in self._SKIP:
            self._skip += 1
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag in self._BLOCK:
            self.parts.append("\n\n")

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip:
            self._skip -= 1
        elif tag.startswith("h") and tag[1:].isdigit():
            self.parts.append("\n\n")

    def handle_data(self, data):
        if self._tag == "title" and not self.title:
            self.title = data.strip()
        if not self._skip and self._tag != "title":
            self.parts.append(data)

    def text(self) -> str:
        raw = "".join(self.parts)
        raw = re.sub(r"[ \t]+", " ", raw)
        return re.sub(r"\n\s*\n+", "\n\n", raw).strip()


def html_to_text(html: str) -> tuple[str, str]:
    parser = _HTMLText()
    parser.feed(html)
    return parser.text(), parser.title


def pdf_to_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages)


def page_url(base_url: str | None, source: str) -> str | None:
    if not base_url:
        return None
    path = re.sub(r"\.(md|markdown|html?|txt|rst)$", "", source)
    path = re.sub(r"(^|/)index$", r"\1", path)
    if path and not path.endswith("/"):
        path += "/"
    return base_url.rstrip("/") + "/" + path


def load_bytes(name: str, data: bytes, base_url: str | None = None) -> Document:
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f"unsupported file type: {name}")
    title = None
    if suffix == ".pdf":
        text = pdf_to_text(data)
    elif suffix in HTML_SUFFIXES:
        text, title = html_to_text(data.decode("utf-8", errors="replace"))
    else:
        text = data.decode("utf-8", errors="replace")
    title = markdown_title(text) or title or Path(name).stem.replace("-", " ").replace("_", " ")
    return Document(source=name, text=text, title=title, url=page_url(base_url, name))


def load_path(path: str | Path, base_url: str | None = None) -> list[Document]:
    root = Path(path)
    files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    docs = []
    for file in files:
        if file.suffix.lower() not in SUPPORTED or file.name.startswith("."):
            continue
        name = file.name if root.is_file() else file.relative_to(root).as_posix()
        doc = load_bytes(name, file.read_bytes(), base_url)
        if doc.text.strip():
            docs.append(doc)
    return docs
