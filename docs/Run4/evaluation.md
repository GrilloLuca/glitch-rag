# Run 4 – Repeatability check (2026-10-30)

Setup as in [Run 1](../evaluation.md): same 20 reviews, same golden set,
`qwen2.5:7b`, `temperature=0`. Only qwen2.5:7b was re-run.

## Change

None. The prompt is identical to [Run 3](../Run3/evaluation.md). The goal is to
measure run-to-run variance: how much the results move when nothing changes.

## Results (qwen2.5:7b)

| Field         | Run 3 | Run 4 (same prompt) |
|---------------|------:|--------------------:|
| sentiment     | 75%   | 75%                 |
| topic         | 60%   | 60%                 |
| is_bug_report | 100%  | 100%                |
| Invalid JSON  | 0/20  | 0/20                |

The wrong reviews are also identical, field by field:
sentiment #1, #3, #7, #10, #17; topic #4, #6, #11, #12, #13, #14, #17, #18.

## Conclusion

- **The classifications are repeatable**: with `temperature=0` on local Ollama,
  the same prompt gives the same labels on this set.
- Therefore the topic fluctuation seen in Runs 1–3 (65% → 55% → 60%) is **not
  random noise**: it is caused by the prompt edits. Changing the sentiment
  definition moved 2–3 topic answers, even though the topic definitions never
  changed. Prompt instructions are coupled.
- Practical rule: after any prompt change, re-measure **all** fields, not only
  the one being targeted.
- Caveat: only one repeat, on one machine. Hosted APIs (e.g. Azure OpenAI) may
  not be deterministic even at `temperature=0`, so repeat this check after the
  move to Azure.

## Next experiment

Run 5: work on topic, which is now the weakest field (60%). Start with the rule
for the most frequent issue: "an effect that looks right in the preview but not
in the saved file → export" (#17 is one of the errors).
