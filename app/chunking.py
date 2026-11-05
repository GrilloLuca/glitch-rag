import hashlib
import re
from dataclasses import dataclass

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    section: str
    text: str


def chunk_id(source: str, section: str, index: int) -> str:
    return hashlib.sha1(f"{source}|{section}|{index}".encode()).hexdigest()[:12]


def split_sections(markdown: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    path: list[str] = []
    lines: list[str] = []

    def flush() -> None:
        body = "\n".join(lines).strip()
        if body:
            sections.append((" > ".join(path), body))
        lines.clear()

    for line in markdown.splitlines():
        match = HEADING_RE.match(line)
        if match:
            flush()
            level = len(match.group(1))
            path[:] = path[: level - 1] + [match.group(2).strip()]
        else:
            lines.append(line)
    flush()
    return sections


def split_long(text: str, max_chars: int, overlap: int) -> list[str]:
    if overlap >= max_chars:
        raise ValueError("overlap must be smaller than max_chars")
    if len(text) <= max_chars:
        return [text]

    pieces: list[str] = []
    current = ""
    for paragraph in (p.strip() for p in text.split("\n\n")):
        if not paragraph:
            continue
        if current and len(current) + len(paragraph) + 2 > max_chars:
            pieces.append(current)
            current = f"{current[-overlap:]}\n\n{paragraph}" if overlap else paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph
    if current:
        pieces.append(current)

    result: list[str] = []
    for piece in pieces:
        while len(piece) > max_chars:
            result.append(piece[:max_chars])
            piece = piece[max_chars - overlap :]
        result.append(piece)
    return result


def chunk_markdown(
    markdown: str, source: str, max_chars: int = 1200, overlap: int = 150
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for section, body in split_sections(markdown):
        for i, piece in enumerate(split_long(body, max_chars, overlap)):
            chunks.append(
                Chunk(id=chunk_id(source, section, i), source=source, section=section, text=piece)
            )
    return chunks