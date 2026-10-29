import json
import sys
from pathlib import Path

FIELDS = ["sentiment", "topic", "is_bug_report"]


def load_by_id(path: Path) -> dict[int, dict]:
    rows = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            rows[row["id"]] = row
    return rows


def main(golden_file: Path, predictions_file: Path) -> None:
    golden = load_by_id(golden_file)
    predictions = load_by_id(predictions_file)

    wrong: dict[str, list[int]] = {field: [] for field in FIELDS}
    false_positives: list[int] = []
    false_negatives: list[int] = []

    for review_id, expected in golden.items():
        predicted = predictions.get(review_id)

        for field in FIELDS:
            expected_value = expected[f"expected_{field}"]
            predicted_value = predicted.get(field) if predicted else None
            if predicted_value != expected_value:
                wrong[field].append(review_id)

        predicted_bug = predicted.get("is_bug_report") if predicted else None
        if predicted_bug is True and expected["expected_is_bug_report"] is False:
            false_positives.append(review_id)
        if predicted_bug is not True and expected["expected_is_bug_report"] is True:
            false_negatives.append(review_id)

    total = len(golden)
    print(f"File: {predictions_file.name}  ({total} recensioni)\n")
    for field in FIELDS:
        correct = total - len(wrong[field])
        print(f"{field:<15} {correct / total:>5.0%}   sbagliati: {wrong[field]}")
    print(f"\nbug falsi positivi: {false_positives}")
    print(f"bug falsi negativi: {false_negatives}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
