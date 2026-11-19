from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, Field

from app.rag import AskResponse


class RagQuestion(BaseModel):
    id: str
    question: str
    category: Literal["howto", "opinion", "unanswerable"]
    expected_doc_ids: list[str] = Field(default_factory=list)
    must_include: list[list[str]] = Field(default_factory=list)


class RagScore(BaseModel):
    id: str
    doc_hit: bool | None
    cited_expected_doc: bool | None
    has_citations: bool
    correct_decline: bool | None
    facts_found: int
    facts_total: int
    missing_facts: list[str]
    invalid_citations: int


def score_answer(question: RagQuestion, response: AskResponse) -> RagScore:
    expected = set(question.expected_doc_ids)
    retrieved = set(response.retrieved_ids)
    cited = {c.id for c in response.citations}
    answer = response.answer.lower()
    missing = [
        alternatives[0]
        for alternatives in question.must_include
        if not any(a.lower() in answer for a in alternatives)
    ]
    return RagScore(
        id=question.id,
        doc_hit=bool(expected & retrieved) if expected else None,
        cited_expected_doc=bool(expected & cited) if expected else None,
        has_citations=bool(cited),
        correct_decline=not cited if question.category == "unanswerable" else None,
        facts_found=len(question.must_include) - len(missing),
        facts_total=len(question.must_include),
        missing_facts=missing,
        invalid_citations=len(response.invalid_citation_ids),
    )


def _count(values: Iterable[bool | None]) -> tuple[int, int]:
    known = [v for v in values if v is not None]
    return sum(known), len(known)


def summarize(scores: list[RagScore]) -> dict[str, tuple[int, int]]:
    answerable = [s for s in scores if s.correct_decline is None]
    return {
        "doc hit@3": _count(s.doc_hit for s in scores),
        "cites expected doc": _count(s.cited_expected_doc for s in scores),
        "answered with citations": _count(s.has_citations for s in answerable),
        "correct declines": _count(s.correct_decline for s in scores),
        "facts included": (
            sum(s.facts_found for s in scores),
            sum(s.facts_total for s in scores),
        ),
    }