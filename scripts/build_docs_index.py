import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

from app.chunking import chunk_markdown
from app.config import get_settings
from app.llm import LLMClient
from app.vector_index import normalize


async def main(src_dir: Path) -> None:
    settings = get_settings()
    chunks = [
        chunk
        for path in sorted(src_dir.glob("*.md"))
        for chunk in chunk_markdown(path.read_text(encoding="utf-8"), path.name)
    ]
    print(f"{len(chunks)} chunk da {src_dir}")
    for c in chunks:
        print(f"  {c.id}  {c.source:<22} {c.section[:60]}  ({len(c.text)} car.)")

    llm = LLMClient(settings)
    try:
        vectors = await llm.embed([f"{c.section}\n\n{c.text}" for c in chunks])
    finally:
        await llm.close()

    out = settings.docs_index_dir
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "embeddings.npy", normalize(np.array(vectors, dtype=np.float32)))
    with (out / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
    print(f"Indice salvato in {out}")


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1])))