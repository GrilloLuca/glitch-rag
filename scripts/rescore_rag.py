import argparse
import json
from pathlib import Path

from app.rag import AskResponse
from app.rag_eval import score_answer, summarize
from scripts.eval_rag import load_questions


def main(questions_file: Path, run_file: Path) -> None:
    questions = {q.id: q for q in load_questions(questions_file)}
    scores = []
    with run_file.open(encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if "error" in record or record["id"] not in questions:
                continue
            response = AskResponse.model_validate(record["response"])
            score = score_answer(questions[record["id"]], response)
            scores.append(score)
            missing = f"  manca: {', '.join(score.missing_facts)}" if score.missing_facts else ""
            print(f"[{score.id:<20}] fatti {score.facts_found}/{score.facts_total}{missing}")

    print(f"\nRicalcolo di {run_file.name} con {questions_file} ({len(scores)} risposte)")
    for name, (ok, total) in summarize(scores).items():
        share = f"({ok / total:.0%})" if total else ""
        print(f"{name:<24} {ok}/{total} {share}")
    print(f"{'invented citations':<24} {sum(s.invalid_citations for s in scores)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ricalcola i punteggi di una run RAG salvata.")
    parser.add_argument("questions", type=Path, help="es. evals/rag_questions.jsonl")
    parser.add_argument("run_file", type=Path, help="es. data/runs/rag_week3-base_qwen2.5_7b.jsonl")
    args = parser.parse_args()
    main(args.questions, args.run_file)
