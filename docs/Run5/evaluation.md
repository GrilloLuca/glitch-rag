# Run 5 – Export definition covers "effect not saved correctly" (2026-10-30)

Setup as in [Run 1](../evaluation.md): same 20 reviews, same golden set,
`qwen2.5:7b`, `temperature=0`. Compared against [Run 4](../Run4/evaluation.md),
the best run so far. Answers in `data/runs/run5_qwen2.5_7b.jsonl`.

## Change

The `export` topic definition was extended:

> export = salvataggio, esportazione, qualità o formato dei file, **e anche un
> effetto che si vede nell'anteprima ma non nel file salvato**

Target: the most common known issue of the app (an effect that does not end up
in the saved image), labelled `export` in the golden set (#9, #10, #17).

## Results (qwen2.5:7b)

| Field         | Run 4 | Run 5 | Δ               |
|---------------|------:|------:|----------------:|
| sentiment     | 75%   | 70%   | −1 review       |
| topic         | 60%   | 65%   | +1 review       |
| is_bug_report | 100%  | 95%   | −1 review       |
| Invalid JSON  | 0/20  | 0/20  | =               |

## What changed, review by review (vs Run 4)

- **topic fixed**: #11 (`other` → `ads_and_purchases`), #14 (`performance` → `export`).
- **topic broken**: #19 (`effects` → `performance`).
- **target missed**: #17, the review the rule was written for, is still
  `performance` instead of `export`.
- **sentiment broken**: #12 (`neutral` → `negative`), although the sentiment
  definition did not change.
- **is_bug_report broken**: #7 is now a false negative, the first bug the 7B
  model has missed. The review says images are not saved in high quality: once
  "quality of the saved file" is framed as an `export` topic, the model no
  longer treats it as a malfunction.

## Conclusion

**Rejected.** The topic gain (+1) is smaller than the losses, and it costs a
missed bug report on the most valuable field, where a false negative is the most
expensive error. The rule also missed its own target (#17). The prompt goes back
to the Run 4 version.

Lesson: the topic definition and the bug definition interact. Describing a
symptom as part of a topic changes whether the model sees it as a bug.

## Next experiment

Run 6: keep the Run 5 export rule **and** state explicitly in `is_bug_report`
that a saved file differing from the preview, or saved in lower quality than
expected, is a malfunction. Accept only if is_bug_report is back to 100%.
