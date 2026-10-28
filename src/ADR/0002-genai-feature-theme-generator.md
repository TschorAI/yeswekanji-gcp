# ADR 0002: GenAI feature: generate a lexical field on the fly

Date: 2026-10-27. Status: Accepted.

## Context

The source app ships 10 hand-curated themes (source ADR 0002) with pre-generated
audio. A learner should be able to type any theme and get cards for it. Two other
GenAI features were considered: a per-card mnemonic and a "question about kanji" Q&A.

## Decision

Feature C, the theme generator:

1. The learner types a theme ("la cuisine").
2. Embed it (`RETRIEVAL_QUERY`), `VECTOR_SEARCH` the 30 nearest of the 1,987 kanji.
3. Gemini picks 10 of the 30 as JSON matching a schema; it may refuse a nonsense
   theme. Python rejects any kanji outside the 30 candidates.
4. Audio for the new cards is generated and cached (audio ADR to come).
5. The theme is saved to the BigQuery `themes` table for the next user.

Evaluation: 10 test themes. Pass = every kanji is in KANJIDIC2, fits the theme,
and nonsense themes are refused.

## Alternatives rejected

- **"Ask a question about kanji" Q&A.** Same retrieval, less use to a learner.
- **Per-card mnemonic.** Kept as optional, only if time remains.
- **Gemini picks kanji without retrieval.** It can return kanji outside the set or
  invented readings; retrieval bounds it to real entries.
- **Claude on Vertex (Model Garden).** Same IAM and billing, but needs Model Garden
  enablement; Gemini Flash-Lite is cheaper and GA on `eu`.

## Consequences

- RAG grounds a generation task, not a Q&A one; citations are the 10 kanji chosen.
- A daily spend counter is needed: a budget alert notifies, it does not cap.
