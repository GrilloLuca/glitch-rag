import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

PER_RATING = 4
SEED = 42
MIN_MONTH = "202301"


def month_of(path: Path) -> str:
    # reviews_<package>_202609.csv -> "202609"
    return path.stem.rsplit("_", 1)[-1]


def main(src_dir: Path, dst: Path) -> None:
    by_rating: dict[int, list[dict]] = defaultdict(list)
    # take all csv starting from 2023
    files = sorted(p for p in src_dir.glob("*.csv") if month_of(p) >= MIN_MONTH)

    for path in files:
        with path.open(encoding="utf-16", newline="") as f:
            for row in csv.DictReader(f):
                text = row.get("Review Text", "").strip()
                if text:
                    by_rating[int(row["Star Rating"])].append(row)

    print(f"Letti {len(files)} file dal {MIN_MONTH}")

    rng = random.Random(SEED)
    sample = []
    for rating in sorted(by_rating):
        rows = by_rating[rating]
        # appending random elements to sample list
        sample.extend(rng.sample(rows, min(PER_RATING, len(rows))))

    with dst.open("w", encoding="utf-8") as out:
        for i, row in enumerate(sample, start=1):
            record = {
                "id": i,
                "rating": int(row["Star Rating"]),
                "language": row["Reviewer Language"],
                "app_version": row["App Version Name"],
                "text": row["Review Text"].strip(),
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Salvate {len(sample)} recensioni in {dst}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
