import csv
import hashlib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReviewRecord:
    id: str
    month: str
    rating: int
    language: str
    app_version: str
    text: str


def month_of(path: Path) -> str:
    return path.stem.rsplit("_", 1)[-1]


def review_id(submitted_millis: str, text: str) -> str:
    return hashlib.sha1(f"{submitted_millis}|{text}".encode()).hexdigest()[:12]


def load_reviews(src_dir: Path, min_month: str = "000000") -> Iterator[ReviewRecord]:
    for path in sorted(src_dir.glob("*.csv")):
        month = month_of(path)
        if month < min_month:
            continue
        with path.open(encoding="utf-16", newline="") as f:
            for row in csv.DictReader(f):
                text = row.get("Review Text", "").strip()
                if not text:
                    continue
                yield ReviewRecord(
                    id=review_id(row["Review Submit Millis Since Epoch"], text),
                    month=month,
                    rating=int(row["Star Rating"]),
                    language=row["Reviewer Language"],
                    app_version=row["App Version Name"],
                    text=text,
                )
