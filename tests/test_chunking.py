from pathlib import Path

import pytest

from app.chunking import chunk_markdown, split_long, split_sections

FAQ = """# Glitch! FAQ

## Exporting

### How do I export in HD?
Tap share and choose 1080p.

### Where are files saved?
In the Pictures/Glitch folder.

## Premium
Premium unlocks all effects.
"""


def test_sections_keep_heading_path():
    sections = split_sections(FAQ)
    assert sections[0] == (
        "Glitch! FAQ > Exporting > How do I export in HD?",
        "Tap share and choose 1080p.",
    )
    assert sections[1][0] == "Glitch! FAQ > Exporting > Where are files saved?"
    assert sections[2] == ("Glitch! FAQ > Premium", "Premium unlocks all effects.")
    assert len(sections) == 3


def test_heading_without_text_produces_no_chunk():
    assert split_sections("# Title\n\n## Empty\n\n## Full\nSome text.") == [
        ("Title > Full", "Some text.")
    ]


def test_short_text_is_not_split():
    assert split_long("short", max_chars=100, overlap=10) == ["short"]


def test_long_text_is_split_by_paragraphs_with_overlap():
    text = "\n\n".join(f"Paragraph {i} " + "x" * 80 for i in range(10))
    pieces = split_long(text, max_chars=300, overlap=40)
    assert len(pieces) > 1
    assert all(len(p) <= 300 for p in pieces)
    assert pieces[0][-40:] in pieces[1]


def test_single_paragraph_longer_than_limit_is_cut():
    pieces = split_long("y" * 750, max_chars=300, overlap=50)
    assert all(len(p) <= 300 for p in pieces)
    assert "".join(p[50:] if i else p for i, p in enumerate(pieces)) == "y" * 750


def test_overlap_must_be_smaller_than_max_chars():
    with pytest.raises(ValueError):
        split_long("x" * 500, max_chars=100, overlap=100)


def test_chunk_ids_are_stable_and_unique():
    first = chunk_markdown(FAQ, "faq.md")
    second = chunk_markdown(FAQ, "faq.md")
    assert [c.id for c in first] == [c.id for c in second]
    assert len({c.id for c in first}) == len(first)


def test_chunk_id_ignores_text_changes():
    original = chunk_markdown(FAQ, "faq.md")
    edited = chunk_markdown(FAQ.replace("1080p", "4K"), "faq.md")
    assert [c.id for c in original] == [c.id for c in edited]


def test_knowledge_base_chunks_are_valid():
    chunks = [
        chunk
        for path in sorted(Path("knowledge").glob("*.md"))
        for chunk in chunk_markdown(path.read_text(encoding="utf-8"), path.name)
    ]
    assert chunks
    assert all(len(c.text) <= 1200 for c in chunks)
    assert len({c.id for c in chunks}) == len(chunks)
