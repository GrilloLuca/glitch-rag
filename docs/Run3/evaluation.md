# Run 3 – Sentiment definition, refined (2026-10-30)

Setup as in [Run 1](../Run1/evaluation.md): same 20 reviews, same golden set,
`qwen2.5:7b`, `temperature=0`. Only qwen2.5:7b was re-run.

## Change

Compared with [Run 2](../Run2/evaluation.md), one clause was added to the
sentiment definition to stop the over-correction on pure complaints:

> sentiment: l'opinione complessiva dell'utente sull'app, non il tono del testo.
> Chi apprezza l'app ma segnala un problema o chiede una modifica è positive;
> **chi si lamenta soltanto è negative.** neutral = opinione tiepida o elogi e
> critiche che si bilanciano.

## Results (qwen2.5:7b)

| Field         | Run 1 | Run 2 | Run 3  |
|---------------|------:|------:|-------:|
| sentiment     | 65%   | 70%   | **75%** |
| topic         | 65%   | 55%   | 60%    |
| is_bug_report | 100%  | 100%  | 100%   |
| Invalid JSON  | 0/20  | 0/20  | 0/20   |

## What changed, review by review (vs Run 1)

Sentiment:
- **Fixed (3)**: #6 and #15 (users who like the app but report a problem or ask
  for a change) and #12 (now `neutral`). Same fixes as Run 2.
- **Over-correction reduced**: #2 (1-star, app stopped working) is `negative`
  again. #3 is still `neutral` instead of `negative`.
- **Still wrong**: #1, #7, #10, #17.

Topic (the topic definitions were not changed in Runs 2 and 3):
- Fixed #5; broke #11 and #14. Compared with Run 2, #5 and #19 went back to
  correct and #14 broke.

## Conclusion

- **Sentiment improved steadily**: 65% → 70% → 75%. The target cases (#6, #15)
  are fixed and stay fixed, and the refinement recovered one of the two pure
  complaints that Run 2 had broken. **Keep this prompt.**
- **Topic fluctuates (65% → 55% → 60%) without any change to its definitions.**
  Editing one part of the prompt moves answers in another part, by about ±2
  reviews. Topic differences of 1–2 reviews between runs should be treated as
  noise, not as an effect of the change.

## Next experiment

Run 4: re-run Run 3 **with no changes** to measure run-to-run variance. If the
results differ, part of the movement in topic is model non-determinism rather
than prompt sensitivity. Then address topic directly (e.g. the
"effect not saved correctly → export" rule).
