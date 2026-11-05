# RAG over reviews – first evaluation (2026-11-04)

`POST /ask` answers a question from the reviews: semantic search retrieves the top 5
reviews, the model answers **only** from them and cites each claim by review id, and the
API checks every cited id against the retrieved reviews (`app/rag.py`).

- **Retrieval**: semantic search, `bge-m3`, k = 5, 11,409 searchable reviews.
- **Generation**: `qwen2.5:7b`, local on Ollama, `temperature=0.2`.
- **Response**: answer, verified `citations`, `invalid_citation_ids` (cited but not
  retrieved), `retrieved_ids` (what the model was given).

## Before and after: "Come esporto un video in HD con Glitch!?"

| | Day 3, no retrieval (`/chat`) | Day 8, RAG (`/ask`) |
|---|---|---|
| Answer | Seven confident steps through menus that do not exist ("Settings → Export → HD", "File → Export → HD") | "The reviews do not explain how to export a video in HD; some users report export problems" |
| Sources | None | 5 retrieved reviews, the claim checkable against them |
| Correct? | No: invented | Yes: it says what the sources do and do not contain |

Same model. The difference comes from the sources and the rules in the prompt.

## Six questions

Retrieval and generation are judged separately, using `retrieved_ids` to read what the
model was given.

| Question | Retrieval | Generation | Faithful? |
|---|---|---|---|
| Export in HD | Partial: where videos are saved, importing, one export problem | Honest "not in the reviews"; the claim about export problems is not cited although a retrieved review supports it | Yes, one uncited claim |
| Problems with datamosh | Good: 5/5 relevant | Uses 3 of 5 (drops "hard to use" and "broken") | Yes |
| What users think of ads | Good: 5/5 complaints, in 4 languages | Cites 1 of 5 and says "some users" when all five complain; does not mention they are from 2015–2017 | Yes, incomplete |
| App freezes when saving a video | Good: 5/5 about saving videos | Merges two reviews into a claim neither makes (freezing *while editing* after premium + videos *not saved*); ignores two relevant reviews | Partly |
| How to change my password | No relevant review (expected) | "No reviews cover this" | Yes |
| Version 4.1.13 | Unrelated reviews about the UI, 2014–2017 | "The reviews do not cover version 4.1.13" | Yes, but 10 reviews of that version exist |

Totals: 0 invented citation ids; 3/3 unanswerable questions correctly declined;
on the 3 questions with good retrieval, the answer uses on average 2 of 5 relevant reviews.

## Findings

- **Hallucination is solved, incomplete synthesis is the new problem.** The model no longer
  invents facts or sources, but it uses only part of what it is given, and once merged two
  sources into an unsupported claim. Retrieval is currently better than generation.
- **Answers list reviews instead of grouping them by theme** ("a user in 2019…, a user in
  2025…") rather than "users report three kinds of problems".
- **Answers vary between runs**: the datamosh answer cited 5 reviews in one run and 3 in the
  next, with the same retrieved reviews, because of `temperature=0.2`. Evaluation runs need
  `temperature=0`.
- **Version questions need a metadata filter**: `app_version` is in the index but search only
  looks at the text.
- **Aggregate questions are out of scope for RAG.** "Which effect had the most bug reports?"
  retrieves generic bug complaints and the model correctly declines. Answering it needs
  classification of every relevant review plus counting, exposed later as a tool for an
  agent (week 5).

## Next experiments

One change at a time, measured on these six questions:

1. `temperature=0` for answers in evaluation runs.
2. Prompt: "use every relevant review and group the information by theme".
3. Metadata filter on `app_version` and on date for recent questions.
4. Keyword and hybrid retrieval on the same questions (`"mode"` in the request).
