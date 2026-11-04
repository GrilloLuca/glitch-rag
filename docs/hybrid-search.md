# Hybrid search – keyword vs semantic vs hybrid (2026-11-03)

Same index as [semantic search](semantic-search.md), now without the 283 reviews that
contain no letters (11,409 searchable reviews). Three modes on the same queries:

- **keyword**: BM25 on lower-cased word tokens (versions such as `4.1.13` kept as one token);
- **semantic**: cosine similarity on `bge-m3` embeddings;
- **hybrid**: reciprocal rank fusion (k = 60) of the top 50 of each mode.

Metric: precision@5, judged by hand with the criterion "would this review help answer the
question?". A mode that returns fewer than 5 results is still divided by 5.

## Results

| Query | Keyword | Semantic | Hybrid | Notes |
|---|---:|---:|---:|---|
| the app crashes when I save a video | 4/5 | 5/5 | 5/5 | Keyword #1 only matches "video" |
| datamosh | 5/5 | 5/5 | 5/5 | Keyword #4 ("Datamosh on the face :)") is slang praise, counted as relevant |
| la mia app preferita | 4/5 | 5/5 | 5/5 | Hybrid returns praise in Spanish, none of semantic's top 5 |
| l'app è cara | 0/5 | 3/5 | 2/5 | Keyword matches Italian praise via "l", "app", "è" |
| VHS | 5/5 | 5/5 | 5/5 | Rare, distinctive term: every mode works |
| troppa pubblicità | 1/5 | 5/5 | 4/5 | Keyword finds only 2 Italian reviews |
| too many ads | 2/5 | 5/5 | 3/5 | Keyword matches "too many paywalls", "too many paid effects" |
| **Total (7 queries)** | **21/35 (60%)** | **33/35 (94%)** | **29/35 (83%)** | |
| 4.1.13 | no results | 0/5 | 0/5 | Correct "no results" from keyword; semantic noise passes into hybrid |

## Findings

- **Semantic search wins on this set; hybrid is second, not first.** Hybrid never beats
  semantic here: it ties on 4 queries and loses on 3.
- **Keyword search hurts on non-English queries.** The corpus is mostly English, so Italian
  function words ("è", "l") are *rare* in it and get a high BM25 weight. Rare in the corpus
  does not mean meaningful.
- **Keyword search hurts on phrases made of common words.** "too many ads" matches "too many
  paywalls": BM25 counts words, not what they refer to.
- **Keyword search helps on distinctive terms** ("datamosh", "VHS") and is the only mode that
  correctly answers "nothing found" ("4.1.13").
- **Equal-weight fusion lets a weak list drag a strong one down.** RRF gives the same weight to
  both rankings even when one of them is poor for that query.
- Caveats: 7 queries, relevance judged on the first 110 characters. Slang and emoji are easy
  to misjudge for someone who does not know the users: one judgment was corrected by the app's author.

## Options to test next

1. **Weighted fusion**: give the keyword ranking a lower weight than the semantic one.
2. **Use keywords only when the query has distinctive terms** (e.g. terms with high IDF that
   are not function words), otherwise semantic only.
3. **Metadata filters** for identifiers such as versions (`app_version = 4.1.13`) instead of search.
4. **A reranker** on the fused candidates (what Azure AI Search's semantic ranker does).

Each option is measured against this table, one change at a time, as in the prompt runs.
