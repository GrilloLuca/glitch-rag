# Run 7 – Configurable app description, refactoring check (2026-11-05)

Setup as in [Run 1](../Run1/evaluation.md): same 20 reviews, same golden set,
`qwen2.5:7b`, `temperature=0`. Compared against [Run 4](../Run4/evaluation.md), the
prompt chosen after Runs 1–6. Answers in `data/runs/run7_qwen2.5_7b.jsonl`.

## Change

A refactoring, not an experiment: the app description now comes from configuration
(`APP_DESCRIPTION`) and is inserted into the prompt template, and the topic definitions
moved to `TOPIC_DEFINITIONS`. The instructions are the same as Run 4, with two side
effects:

- the opening lines of the prompt were reflowed (different line breaks);
- the rejected Run 6 bug rule, which had been committed by mistake, was removed.

The goal is to check that the refactoring does not change behaviour.

## Results (qwen2.5:7b)

| Field         | Run 4 | Run 7 | Δ         |
|---------------|------:|------:|----------:|
| sentiment     | 75%   | 75%   | =         |
| topic         | 60%   | 65%   | +1 review |
| is_bug_report | 100%  | 100%  | =         |
| Invalid JSON  | 0/20  | 0/20  | =         |

Only one answer changed: topic #13 (`effects` → `other`), now correct. Sentiment errors
(#1, #3, #7, #10, #17) and bug-report answers are identical to Run 4.

## Conclusion

**No regression; Run 7 is the new reference prompt.** The single change is consistent
with what Runs 2–6 showed: even edits that do not change the instructions, such as line
breaks, can move one borderline answer. A refactoring of a prompt is checked against the
golden set like any other change.
