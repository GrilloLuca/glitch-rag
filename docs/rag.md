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

---

# Run 2 – Documentation as a second source (2026-11-05)

The knowledge base in `knowledge/` (FAQ, effects, store description) is split by heading
into 44 chunks (`app/chunking.py`), embedded with the section path, and searched next to
the reviews. The prompt separates `<documentation>` (official: how the app works) from
`<reviews>` (user experiences) and asks to state disagreements between them.

- **Retrieval**: semantic, top 3 documentation chunks + top 5 reviews.
- **Generation**: `qwen2.5:7b`, `temperature=0` (Run 1 used 0.2: a second variable changed).

## The six questions of Run 1

| Question | Run 1 (reviews only) | Run 2 (+ documentation) | |
|---|---|---|---|
| Export in HD | "Not in the reviews" | Correct answer from the FAQ, 4/4 claims faithful; omits that both tools are premium | Much better |
| Problems with datamosh | 3 of 5 reviews used | 5 of 5, grouped by kind of problem; does not say the documentation confirms it is premium | Better |
| What users think of ads | 1 of 5 reviews used | 3 of 5, but reads "ads are annoying" as positive and concludes users are "divided" when all five complain | Not faithful |
| App freezes when saving a video | Two reviews merged into one claim | Three reviews merged into a claim only one of them makes | Not faithful |
| How to change my password | Declined | Declined, suggests contacting support | Same |
| Version 4.1.13 | Declined | Declined | Same |

## Four questions for the documentation

| Question | Top documentation chunk | Answer | Faithful? |
|---|---|---|---|
| Where are videos saved? | FAQ "Where are my photos and videos saved?" (1st) | `Movies/ImageGlitcher`, also in the gallery | Yes |
| What does premium include? | FAQ "What does the premium version include?" (1st) | All premium effects and higher photo resolutions; omits the list of premium effects and the plans | Yes, incomplete |
| Is Datamosh free? | Effects "Datamosh: Access: Premium" (1st) | "No, it requires premium" (2 documentation chunks) and "some users asked for it to be free" (4 reviews) | Yes: the best answer of the run |
| Which formats can I export? | FAQ on HD export (1st), FAQ on formats (2nd) | JPG for photos; MP4, GIF "or Datamosh" for videos: Datamosh is an effect, not a format | No, one error |

## Totals

| | Run 1 (6 questions) | Run 2 (10 questions) |
|---|---:|---:|
| Fabricated citation ids | 0 | 0 |
| Unanswerable questions correctly declined | 3/3 | 2/2 |
| Answers fully faithful | 3/6 (export, password, version) | 7/10 |
| Right documentation chunk ranked 1st or 2nd | – | 5/5 |

## Findings

- **Documentation solves "how do I" questions**: export, save location, premium, formats.
  The right chunk was ranked 1st in 4 of 5 cases and 2nd in the other.
- **Documentation and reviews combine well when the question asks for both.** "Is Datamosh
  free?" cites the official answer and the user requests separately. When the question
  only asks about users ("what problems do users report"), the model ignores the
  documentation, even when it confirms the reviews.
- **Faithfulness errors are about what sources say, not what they are about.** Retrieval
  finds the right topic; the model then misreads polarity ("annoying"), merges different
  complaints into one claim, or mixes up concepts (an effect listed as a format).
- **Answers are faithful but incomplete**: key facts in the cited chunk are left out
  (the premium requirement for HD video, the list of premium effects).
- **Documentation retrieval always returns 3 chunks**, even when no chunk is relevant
  (ads, password): three slots of irrelevant context.

## Next experiments

1. Prompt rule: "each sentence describes only what the sources cited in it say".
2. A golden set of expected facts per question, to measure completeness (week 3).
3. A similarity threshold, calibrated on this index, to drop documentation chunks below the
   noise level.

---

# Run 3 – Automated end-to-end evaluation (2026-11-18)

The manual evaluation of Run 2 is now a command. `evals/rag_questions.jsonl` holds the
10 questions with their category, the documentation chunks that should be retrieved and
the facts the answer must contain. `scripts/eval_rag.py` runs every question through the
same `answer_question` used by `/ask` (no HTTP server), scores it with the pure function
`score_answer` (`app/rag_eval.py`) and saves question, full response, score and latency
to `data/runs/rag_<run>_<model>.jsonl`.

```bash
uv run python -m scripts.eval_rag evals/rag_questions.jsonl week2
```

- **Retrieval**: semantic, top 3 documentation chunks + top 5 reviews (as in Run 2).
- **Generation**: `qwen2.5:7b`, `temperature=0`, local on Ollama, CPU only (Intel Mac).

## Metrics

| Metric | What it checks |
|---|---|
| Doc hit@3 | An expected documentation chunk is among the 3 retrieved (how-to questions) |
| Cites expected doc | The answer cites that chunk |
| Answered with citations | Answerable questions cite at least one source |
| Correct declines | Unanswerable questions cite nothing |
| Facts included | Expected facts found in the answer: each fact is a list of alternatives, case-insensitive substring match |
| Invented citations | Cited ids that were not retrieved |

A metric that does not apply to a question (doc hit for an opinion question, decline for
an answerable one) is `None` and is left out of the totals.

## Baseline: week 2

| Metric | Result |
|---|---:|
| Doc hit@3 | 5/5 (100%) |
| Cites expected doc | 5/5 (100%) |
| Answered with citations | 8/8 (100%) |
| Correct declines | 2/2 (100%) |
| Facts included | 13/16 (81%) |
| Invented citations | 0 |
| Errors | 0 |
| Seconds per question | 59.2 on average; 52.7 without the first question (117.6 s, model loading) |

The three missing facts are all real omissions:

- **Export in HD**: no mention that Datamosh and Video are premium (seen by hand in Run 2).
- **Premium content**: no premium effect named.
- **App freezes when saving**: the answer cites three reviews (a freeze while *editing*,
  videos *not saved*, videos *saved with errors*), merges them into "yes, it is a known
  problem" and keeps only the one that is not about saving.

Answers are identical word for word across three runs at `temperature=0`; only latency
changes. Retrieval and citation numbers match the manual Run 2.

## What the automatic metrics cannot see

Keyword facts measure **presence, not correctness**. Two answers pass every automatic
check and are still not faithful:

- **Ads**: "users are divided" when every retrieved review complains, yet the fact
  "annoying" is found.
- **Formats**: "MP4, GIF or Datamosh" lists an effect as a format, yet JPG, MP4 and GIF
  are all found.

Manual faithfulness is unchanged from Run 2: 7/10. Automating it (a second model as a
judge, checked against these manual labels) is the next step.

## Lessons on writing expected facts

The first two versions of the facts scored 10/14 and 11/13 on the same answers: the
differences were measurement errors, not model changes.

- **No alternative may appear in the question.** "video" in the facts for "How do I
  export a video in HD?" is always found, so the fact measures nothing.
- **Use stems, not words.** "risoluzione" does not match "risoluzioni"; "risoluz" matches
  both.
- **Match the answer's language, or use language-independent terms.** English keywords
  ("effects") against Italian answers ("effetti") fail on correct answers. Numbers, file
  formats, paths and effect names work in every language.
- **An alternative counts as much as the others.** `["animation", "datamosh", "premium"]`
  is satisfied by the word "Datamosh" alone, so the premium omission disappears from the
  numbers. A fact that must be checked has to stand alone.

## Next experiments

1. LLM-as-a-judge faithfulness, validated against the manual labels of Runs 2 and 3.
2. A larger question set (week 3), with more opinion questions.
3. Prompt rule: "each sentence describes only what the sources cited in it say",
   measured with this command.
