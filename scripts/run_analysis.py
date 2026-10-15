import asyncio
import json
import sys
import time
from pathlib import Path

from app.analysis import analyze_review
from app.config import get_settings
from app.llm import LLMClient, LLMError


async def main(src: Path) -> None:
    settings = get_settings()
    llm = LLMClient(settings)
    model_tag = settings.llm_model.replace(":", "_")
    dst = src.with_name(f"analysis_{model_tag}.jsonl")
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
    print(f"\nModello: {settings.llm_model}  OK: {ok}  Falliti: {failed}")
    print(f"Tempo totale: {elapsed:.1f}s  →  {dst}")


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1])))
