import json
from datetime import UTC, datetime
from pathlib import Path

META_FILE = "index_meta.json"


class IndexMismatchError(RuntimeError):
    """L'indice su disco non corrisponde alla configurazione o è incompleto."""


def write_index_meta(index_dir: Path, embedding_model: str, count: int, dimensions: int) -> None:
    meta = {
        "embedding_model": embedding_model,
        "count": count,
        "dimensions": dimensions,
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (index_dir / META_FILE).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def check_index_meta(index_dir: Path, embedding_model: str, count: int, dimensions: int) -> None:
    path = index_dir / META_FILE
    if not path.exists():
        raise IndexMismatchError(f"{path} mancante: ricostruisci l'indice.")
    meta = json.loads(path.read_text(encoding="utf-8"))
    if meta["embedding_model"] != embedding_model:
        raise IndexMismatchError(
            f"{index_dir} è stato costruito con {meta['embedding_model']!r}, "
            f"ma EMBEDDING_MODEL è {embedding_model!r}: ricostruisci l'indice."
        )
    if (meta["count"], meta["dimensions"]) != (count, dimensions):
        raise IndexMismatchError(
            f"{index_dir}: i metadati dicono {meta['count']}×{meta['dimensions']}, "
            f"i file contengono {count}×{dimensions}: indice incompleto o file mescolati."
        )