from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

_NAMESPACE = uuid.UUID("6f1c3c0e-8a52-4b0e-9a57-2d0c1f4b9e11")
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_ANCHOR = re.compile(r"\s*\{\s*#([\w\-]+)\s*\}\s*$")
_FENCE = re.compile(r"^\s*(```|~~~)")
_SENTENCE = re.compile(r"(?<=[.!?…])\s+")


@dataclass
class Document:
    source: str
    text: str
    title: str = ""
    url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def hash(self) -> str:
        return hashlib.sha1(self.text.encode()).hexdigest()


@dataclass
class Chunk:
    id: str
    source: str
    title: str
    section: str
    text: str
    position: int
    url: str | None = None
    doc_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def header(self) -> str:
        return f"{self.title} — {self.section}" if self.section else self.title

    def indexed_text(self) -> str:
        return f"{self.header}\n\n{self.text}" if self.header else self.text

    def payload(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "title": self.title,
            "section": self.section,
            "text": self.text,
            "position": self.position,
            "url": self.url,
            "doc_hash": self.doc_hash,
            **self.metadata,
        }


@dataclass
class _Block:
    text: str
    level: int = 0
    heading: str = ""
    anchor: str | None = None


def parse_heading(line: str) -> tuple[int, str, str | None] | None:
    match = _HEADING.match(line)
    if not match:
        return None
    title = match.group(2)
    anchor = _ANCHOR.search(title)
    if anchor:
        title = title[: anchor.start()].strip()
    return len(match.group(1)), title.strip(), anchor.group(1) if anchor else None


def markdown_title(text: str) -> str | None:
    in_fence = False
    for line in text.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and (h := parse_heading(line)) and h[0] == 1:
            return h[1]
    return None


def _blocks(text: str) -> list[_Block]:
    blocks: list[_Block] = []
    buf: list[str] = []
    in_fence = False

    def flush() -> None:
        if buf and "".join(buf).strip():
            blocks.append(_Block("\n".join(buf).strip("\n")))
        buf.clear()

    for line in text.splitlines():
        if in_fence:
            buf.append(line)
            if _FENCE.match(line):
                in_fence = False
                flush()
            continue
        if _FENCE.match(line):
            flush()
            buf.append(line)
            in_fence = True
            continue
        heading = parse_heading(line)
        if heading:
            flush()
            level, title, anchor = heading
            blocks.append(_Block(line.strip() if not anchor else "#" * level + " " + title, level, title, anchor))
        elif not line.strip():
            flush()
        else:
            buf.append(line)
    flush()
    return blocks


def _split_long(text: str, size: int) -> list[str]:
    if len(text) <= size:
        return [text]
    is_code = bool(_FENCE.match(text))
    units = text.split("\n") if is_code else _SENTENCE.split(text)
    sep = "\n" if is_code else " "
    pieces: list[str] = []
    cur = ""
    for unit in units:
        while len(unit) > size:
            cut = unit.rfind(" ", 0, size)
            cut = cut if cut > size // 2 else size
            unit_head, unit = unit[:cut], unit[cut:].lstrip()
            if cur:
                pieces.append(cur)
                cur = ""
            pieces.append(unit_head)
        if cur and len(cur) + len(sep) + len(unit) > size:
            pieces.append(cur)
            cur = unit
        else:
            cur = f"{cur}{sep}{unit}" if cur else unit
    if cur:
        pieces.append(cur)
    return pieces


class Chunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 150, min_size: int | None = None):
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_size = min_size if min_size is not None else chunk_size // 4

    def split(self, doc: Document) -> list[Chunk]:
        title = doc.title or markdown_title(doc.text) or doc.source
        path: list[_Block] = []
        chunks: list[Chunk] = []
        cur: list[str] = []
        state = {"section": "", "anchor": None}

        def section_of() -> tuple[str, str | None]:
            names = [b.heading for b in path if not (b.level == 1 and b.heading == title)]
            anchor = next((b.anchor for b in reversed(path) if b.anchor), None)
            return " > ".join(names), anchor

        def start() -> None:
            state["section"], state["anchor"] = section_of()

        def length() -> int:
            return sum(len(x) for x in cur) + 2 * max(len(cur) - 1, 0)

        def emit() -> None:
            text = "\n\n".join(cur).strip()
            if not text or all(_HEADING.match(x) for x in cur):
                return
            url = doc.url
            if url and state["anchor"]:
                url = f"{url}#{state['anchor']}"
            position = len(chunks)
            chunks.append(
                Chunk(
                    id=str(uuid.uuid5(_NAMESPACE, f"{doc.source}#{position}")),
                    source=doc.source,
                    title=title,
                    section=state["section"],
                    text=text,
                    position=position,
                    url=url,
                    doc_hash=doc.hash,
                    metadata=dict(doc.metadata),
                )
            )

        for block in _blocks(doc.text):
            if block.level:
                if length() >= self.min_size:
                    emit()
                    cur.clear()
                while path and path[-1].level >= block.level:
                    path.pop()
                path.append(block)
                if not cur:
                    start()
                if not (block.level == 1 and block.heading == title):
                    cur.append(block.text)
                continue
            for piece in _split_long(block.text, self.chunk_size):
                if cur and length() + 2 + len(piece) > self.chunk_size:
                    emit()
                    tail = cur[-1]
                    carry = tail if len(tail) <= self.overlap and not _HEADING.match(tail) else None
                    cur.clear()
                    start()
                    if carry and len(carry) + 2 + len(piece) <= self.chunk_size:
                        cur.append(carry)
                if not cur:
                    start()
                cur.append(piece)
        emit()
        return chunks
