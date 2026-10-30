# Review analysis – evaluation log

Each run classifies the same 20 Play Store reviews of Glitch! and compares the
model output with a hand-labelled golden set (`data/golden.jsonl`, not committed:
it contains user reviews).

## Setup

- **Sample**: 20 reviews with text, submitted from January 2023 onwards,
  4 per star rating (1–5), fixed seed (`scripts/sample_reviews.py`).
- **Fields**: `sentiment` (3 classes), `topic` (6 classes), `is_bug_report` (bool).
- **Output**: schema-constrained JSON, validated with Pydantic (`app/analysis.py`).
- **Runtime**: Ollama, local, `temperature=0`.
- **Metric**: accuracy per field (`scripts/evaluate.py`). Failed or missing
  answers count as wrong. With 20 reviews, one review = 5 percentage points.

## Run 1 – Baseline (2026-10-29)

Prompt: initial version.

| Field         | qwen2.5:1.5b | qwen2.5:7b |
|---------------|-------------:|-----------:|
| sentiment     | 65%          | 65%        |
| topic         | 40%          | 65%        |
| is_bug_report | 80%          | **100%**   |
| Invalid JSON  | 0 / 20       | 0 / 20     |

Bug reports: 1.5b missed 2 (false negatives) and raised 2 false alarms;
7b made no mistakes.

### Findings

- **Schema-constrained output works**: no invalid answers, even from the 1.5B model.
  Errors are about content, not format.
- **The 1.5B model collapses onto one class**: it labelled 14/20 reviews as
  `effects` and never used `export` or `other`.
- **Sentiment errors are systematic, not random**: 6 of the 7 errors are shared
  by both models. The labels judge the user's overall opinion of the app, while
  the models judge the tone of the text (a user who likes the app but reports a
  bug is labelled `negative`). The prompt does not say which criterion to use.
- **The golden set had labelling errors**: reviewing the disagreements showed
  three generic-praise reviews labelled `performance`. After fixing the labels,
  7b topic accuracy went from 55% to 65%.
- **Decision**: 7b is better or equal on every field; further experiments use 7b only.

## Next experiment

Run 2: add an explicit definition of sentiment to the prompt ("overall opinion
of the app, not the tone of the text"). Change nothing else, re-run 7b, and check
that `topic` and `is_bug_report` do not regress.
