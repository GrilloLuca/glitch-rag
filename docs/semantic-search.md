# Semantic search – first look (2026-11-03)

Vector search over the full review history, before any keyword search or filtering.

## Setup

- **Index**: 11,692 reviews with text (December 2013 – September 2026), one review = one vector.
- **Embedding model**: `bge-m3` (multilingual, 1024 dimensions), local on Ollama.
  Building the index took 295 s (about 40 reviews/s) and is done once.
- **Search**: cosine similarity on normalised vectors, in memory with numpy
  (`app/vector_index.py`, `scripts/search.py`).
- **Metric**: precision@5 = relevant results among the top 5 ÷ 5, judged by hand.
  Criterion: "would this review help answer the question?"

## Results

| Query | Language | Precision@5 | Top score | Notes |
|---|---|---:|---:|---|
| the app crashes when I save a video | en | 5/5 (100%) | 0.790 | Finds reviews without the word "crash" and in other languages (pt) |
| datamosh | – | 5/5 (100%) | 0.792 | Rare, distinctive term; surfaces two themes: hard to use, and paid |
| la mia app preferita | it | 5/5 (100%) | 0.938 | Near-paraphrases in four languages |
| l'app è cara | it | 3/5 (60%) | 0.802 | Two off-topic results score almost as high as relevant ones (0.767–0.768) |
| 4.1.13 | – | 0/5 (0%) | 0.617 | Returns five identical "." reviews; no review mentions a version in its text |

Mean precision@5: **73%** (18/25).

## Findings

- **Meaning over words**: semantic search matches paraphrases and works across languages,
  including Italian queries over mostly English reviews.
- **Scores rank, they do not judge**: relevant and off-topic results can differ by
  0.03, so a fixed similarity threshold cannot tell them apart.
- **Vector search never returns "nothing found"**: an unanswerable query still returns
  five results, just with lower scores. The RAG step must handle this.
- **Identifiers need a different tool**: version numbers have almost no meaning for the
  embedding model, and the version lives in the `app_version` field, not in the text
  (10 reviews have `app_version = 4.1.13`, 0 mention it). Questions about a version are a
  **metadata filter**, not a search.
- **Old reviews dominate**: most reviews with text are from 2016–2019 (only 116 since
  2023), so results describe older versions of the app. Recency will need a filter or a weight.
- **`Reviewer Language` is the device language, not the language of the text**: not usable
  as a language filter.

## Data quality

| Group | Reviews | Share |
|---|---:|---:|
| No letters at all (".", emoji, ":)") | 283 | 2.4% |
| Letters but under 10 characters ("Best app", "Cool") | 2,791 | 23.9% |

Reviews with no letters are pure noise: they answer no question and take result slots on
vague queries, as the "4.1.13" query shows. Short reviews carry a sentiment but no content.
Both are candidates for exclusion; the threshold will be measured, not guessed.

## Next

Day 7: hybrid search (BM25 keywords + vectors), compared with this table on the same queries.
