import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from app.analysis import analyze_review
from app.config import get_settings
from app.llm import LLMClient, LLMError

RUNS_DIR = Path("data/runs")


async def main(src: Path, run_name: str, force: bool) -> None:
    settings = get_settings()
    model_tag = settings.llm_model.replace(":", "_")
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    dst = RUNS_DIR / f"{run_name}_{model_tag}.jsonl"

    if dst.exists() and not force:
        sys.exit(
            f"{dst} esiste già: scegli un altro nome per la run "
            "oppure usa --force per sovrascriverlo."
        )

    llm = LLMClient(settings)
    ok = failed = 0
    started = time.perf_counter()

    try:
        with src.open(encoding="utf-8") as f, dst.open("w", encoding="utf-8") as out:
            for line in f:
                review = json.loads(line)
                try:
                    analysis = await analyze_review(llm, review["text"])
                    result = {"id": review["id"], **analysis.model_dump()}
                    ok += 1
                except LLMError as e:
                    result = {"id": review["id"], "error": str(e)}
                    failed += 1
                out.write(json.dumps(result, ensure_ascii=False) + "\n")
                print(f"[{review['id']:>2}] {review['rating']}★ → {result}")
    finally:
        await llm.close()

    elapsed = time.perf_counter() - started
    print(
        f"\nRun: {run_name}  Modello: {settings.llm_model}  OK: {ok}  Falliti: {failed}"
    )
    print(f"Tempo totale: {elapsed:.1f}s  →  {dst}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analizza un campione di recensioni con l'LLM."
    )
    parser.add_argument(
        "src", type=Path, help="file JSONL con le recensioni, es. data/sample.jsonl"
    )
    parser.add_argument("run_name", help="nome della run, es. run5")
    parser.add_argument(
        "--force", action="store_true", help="sovrascrive una run esistente"
    )
    args = parser.parse_args()
    asyncio.run(main(args.src, args.run_name, args.force))
