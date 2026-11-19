import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from app.config import get_settings
from app.llm import LLMClient, LLMError
from app.rag import AskRequest, answer_question
from app.rag_eval import RagQuestion, score_answer, summarize
from app.search import ReviewSearch

RUNS_DIR = Path("data/runs")


def load_questions(path: Path) -> list[RagQuestion]:
    with path.open(encoding="utf-8") as f:
        return [RagQuestion.model_validate_json(line) for line in f if line.strip()]


async def main(questions_file: Path, run_name: str, mode: str, force: bool) -> None:
    settings = get_settings()
    model_tag = settings.llm_model.replace(":", "_")
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    dst = RUNS_DIR / f"rag_{run_name}_{model_tag}.jsonl"
    if dst.exists() and not force:
        sys.exit(f"{dst} esiste già: scegli un altro nome o usa --force.")

    questions = load_questions(questions_file)
    search = ReviewSearch.load(settings.index_dir)
    try:
        docs = ReviewSearch.load(settings.docs_index_dir, records="chunks.jsonl")
    except FileNotFoundError:
        docs = None
        print("Attenzione: indice della documentazione assente")

    llm = LLMClient(settings)
    scores = []
    errors = 0
    total_seconds = 0.0
    try:
        with dst.open("w", encoding="utf-8") as out:
            for q in questions:
                started = time.perf_counter()
                try:
                    response = await answer_question(
                        llm, search, docs, AskRequest(question=q.question, mode=mode)
                    )
                except LLMError as e:
                    errors += 1
                    out.write(json.dumps({"id": q.id, "error": str(e)}) + "\n")
                    print(f"[{q.id}] ERRORE: {e}")
                    continue
                seconds = time.perf_counter() - started
                total_seconds += seconds
                score = score_answer(q, response)
                scores.append(score)
                record = {
                    "id": q.id,
                    "question": q.question,
                    "seconds": round(seconds, 1),
                    "score": score.model_dump(),
                    "response": response.model_dump(),
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                missing = f"  manca: {', '.join(score.missing_facts)}" if score.missing_facts else ""
                print(
                    f"[{q.id:<18}] {seconds:6.1f}s  fatti {score.facts_found}/{score.facts_total}"
                    f"  citazioni {len(response.citations)}{missing}"
                )
    finally:
        await llm.close()

    print(f"\nRun: {run_name}  Modello: {settings.llm_model}  Modalità: {mode}")
    for name, (ok, total) in summarize(scores).items():
        share = f"({ok / total:.0%})" if total else ""
        print(f"{name:<24} {ok}/{total} {share}")
    print(f"{'invented citations':<24} {sum(s.invalid_citations for s in scores)}")
    print(f"{'errors':<24} {errors}")
    if scores:
        print(f"{'avg seconds/question':<24} {total_seconds / len(scores):.1f}")
    print(f"→ {dst}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Valutazione end-to-end del RAG.")
    parser.add_argument("questions", type=Path, help="es. evals/rag_questions.jsonl")
    parser.add_argument("run_name", help="es. week2")
    parser.add_argument("--mode", choices=["semantic", "hybrid"], default="semantic")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.questions, args.run_name, args.mode, args.force))