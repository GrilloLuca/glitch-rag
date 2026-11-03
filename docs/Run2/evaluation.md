# Run 2 – Explicit sentiment definition (2026-10-30)

Setup as in [Run 1](../Run1/evaluation.md): same 20 reviews, same golden set,
`qwen2.5:7b`, `temperature=0`. Only qwen2.5:7b was re-run.

## Change

One line of the system prompt (`app/analysis.py`). The sentiment definition went from

> sentiment: positive, neutral o negative.

to

> sentiment: l'opinione complessiva dell'utente sull'app, non il tono del testo.
> Chi apprezza l'app ma segnala un problema o chiede una modifica è positive.
> neutral = opinione tiepida o elogi e critiche che si bilanciano.

## Results (qwen2.5:7b)

| Field         | Run 1 (baseline) | Run 2  | Δ          |
|---------------|-----------------:|-------:|-----------:|
| sentiment     | 65%              | 70%    | +5 (+1 review) |
| topic         | 65%              | 55%    | −10 (−2 reviews) |
| is_bug_report | 100%             | 100%   | =          |
| Invalid JSON  | 0 / 20           | 0 / 20 | =          |

## What changed, review by review

Sentiment:
- **Fixed (3)**: #6 and #15 (users who like the app but report a problem or ask
  for a change, the exact case the rule targets) and #12 (now `neutral`).
- **Broken (2)**: #2 and #3, two 1-star reviews that only say the app stopped
  working, went from `negative` to `neutral`. The phrase "segnala un problema"
  made the model soften pure complaints.
- **Still wrong**: #1, #7, #17. #10 changed answer but is still wrong
  (`negative` → `positive`, expected `neutral`).

Topic (the prompt for topic was not changed):
- **Broken (2)**: #11 (`ads_and_purchases` → `other`) and #19 (`effects` →
  `performance`). Side effect: instructions in a prompt influence each other.

## Conclusion

Net effect: +1 review on sentiment, −2 on topic. With 20 reviews this is within
noise, so the change is **not a clear improvement**. The rule fixes its target
cases but over-corrects pure complaints.

## Next experiment

Run 3: refine the wording so that a review which only complains is still
negative, e.g. "Chi apprezza l'app ma segnala un problema è positive; chi si
lamenta soltanto è negative." Re-run 7b and compare against both Run 1 and Run 2.
