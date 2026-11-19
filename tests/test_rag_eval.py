from app.rag import AskResponse, Citation
from app.rag_eval import RagQuestion, score_answer, summarize


def make_response(answer: str, cited: list[str], retrieved: list[str]) -> AskResponse:
    return AskResponse(
        answer=answer,
        citations=[Citation(id=c, kind="doc", text="") for c in cited],
        invalid_citation_ids=[],
        retrieved_ids=retrieved,
        model="fake",
    )


HOWTO = RagQuestion(
    id="export-hd",
    question="Come esporto in HD?",
    category="howto",
    expected_doc_ids=["e388a88fdb23"],
    must_include=[["MP4"], ["1280"], ["premium"]],
)
UNANSWERABLE = RagQuestion(id="password", question="Password?", category="unanswerable")


def test_howto_answer_with_missing_fact():
    response = make_response(
        "Salva in mp4, al massimo 1280 pixel [e388a88fdb23]",
        cited=["e388a88fdb23"],
        retrieved=["e388a88fdb23", "aaaaaaaaaaaa"],
    )
    score = score_answer(HOWTO, response)
    assert score.doc_hit is True
    assert score.cited_expected_doc is True
    assert (score.facts_found, score.facts_total) == (2, 3)
    assert score.missing_facts == ["premium"]
    assert score.correct_decline is None


def test_fact_alternatives_count_once():
    question = HOWTO.model_copy(update={"must_include": [["pag", "pay", "premium"]]})
    score = score_answer(question, make_response("Devi pagare, è premium", [], []))
    assert (score.facts_found, score.facts_total) == (1, 1)


def test_wrong_document_retrieved():
    score = score_answer(HOWTO, make_response("...", cited=[], retrieved=["bbbbbbbbbbbb"]))
    assert score.doc_hit is False
    assert score.cited_expected_doc is False


def test_unanswerable_question_declined_or_not():
    declined = score_answer(UNANSWERABLE, make_response("Non lo so", [], ["x"]))
    answered = score_answer(UNANSWERABLE, make_response("Vai su [ccc]", ["cccccccccccc"], []))
    assert declined.correct_decline is True
    assert answered.correct_decline is False
    assert declined.doc_hit is None


def test_summary_ignores_metrics_that_do_not_apply():
    scores = [
        score_answer(HOWTO, make_response("mp4 1280 premium", ["e388a88fdb23"], ["e388a88fdb23"])),
        score_answer(UNANSWERABLE, make_response("Non lo so", [], [])),
    ]
    summary = summarize(scores)
    assert summary["doc hit@3"] == (1, 1)
    assert summary["correct declines"] == (1, 1)
    assert summary["answered with citations"] == (1, 1)
    assert summary["facts included"] == (3, 3)