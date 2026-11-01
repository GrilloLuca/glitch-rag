# Run 6 – Explicit bug definition for saved-file issues (2026-10-30)

Setup as in [Run 1](../evaluation.md): same 20 reviews, same golden set,
`qwen2.5:7b`, `temperature=0`. Compared against [Run 4](../Run4/evaluation.md).
Answers in `data/runs/run6_qwen2.5_7b.jsonl`.

## Change

Starting from the Run 4 prompt (the Run 5 export rule had been reverted), one
sentence was added to the `is_bug_report` definition:

> … Una lamentela su prezzi o pubblicità non è un bug, **mentre un file salvato
> diverso dall'anteprima, o di qualità inferiore, è un bug.**

Note: the plan in Run 5 was to test this rule *together with* the export rule.
This run tests the bug rule **alone**.

## Results (qwen2.5:7b)

| Field         | Run 4 | Run 6 | Δ         |
|---------------|------:|------:|----------:|
| sentiment     | 75%   | 75%   | =         |
| topic         | 60%   | 55%   | −1 review |
| is_bug_report | 100%  | 100%  | =         |
| Invalid JSON  | 0/20  | 0/20  | =         |

Only one answer changed: topic #19 (`effects` → `performance`), now wrong.
#19 also flipped to `performance` in Run 5: it is a fragile review that moves
with almost any prompt edit.

## Conclusion

**Rejected.** On its own the rule brings nothing (is_bug_report was already at
100% in Run 4) and costs one topic answer. Prompt goes back to Run 4.

## Where the prompt tuning stands

After six runs the best prompt is still Run 4 (sentiment 75%, topic 60%,
bug reports 100%). Recent changes move one review at a time, which on a
20-review set cannot be told apart from prompt sensitivity. Further tuning needs
a larger golden set (planned for week 3) rather than more edits on this one.
