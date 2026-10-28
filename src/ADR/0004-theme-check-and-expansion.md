# ADR 0004: Step 0 checks the theme and expands it before retrieval; k = 30

Date: 2026-10-28. Status: Accepted.

## Context

Test set v1 (10 themes) scored 7/10. Two failures were requests that are not themes
("le nom de mon chat", "le cours du Bitcoin demain"): Gemini reinterpreted them. One
was retrieval recall: for "la météo", 雲 ranked 33rd, outside the 30 candidates.
Fix: validate the theme before the search.

## Decision

Add step 0, one Gemini call (`gemini-3.5-flash-lite`, temperature 0, JSON schema):

- **Check:** refuse gibberish, questions and requests for information (prices,
  forecasts, facts), personal data, offensive content.
- **Expand:** if accepted, return the theme plus 10-15 simple related French words.
  The expanded text is embedded instead of the bare theme (query expansion).

Keep **k = 30** candidates.

Measured, 10 themes x 3 runs (`src/eval_themes.py`):

| config | pass | tokens |
|---|---|---|
| no step 0, k=30 | 21/30 | 47,971 |
| step 0, k=30 | 30/30 | 44,619 |
| step 0, k=50 | 30/30 | 58,075 |

## Alternatives rejected

- **k = 50.** Same score, 30 % more tokens. Kept as the first fix if recall drops.
- **Distance threshold to refuse.** Nonsense scored 0.41 vs 0.27-0.40 for real
  themes: no usable cut.
- **Refusal left to the select step only.** Gemini reinterprets loose requests there.

## Consequences

- One more call per theme: about 0.5-1.5 s and ~350 tokens; refused themes stop
  before retrieval, so total tokens went down.
- 30/30 is a training score: step 0 was designed on these themes. A held-out set is
  needed before claiming it generalises.
- École sits at the limit (10 acceptable candidates for 10 picks in one run).
