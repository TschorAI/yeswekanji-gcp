# ADR 0001: Regions: BigQuery `EU`, Vertex AI `eu`, Cloud Run `europe-west1`

Date: 2026-10-27. Status: Accepted.

## Context

Users and data are in Europe: keep data and model calls in an EU region where the
Gemini models are available, checked in the docs and with live calls.

## Decision

- Gemini: `gemini-3.5-flash-lite` (GA 2026-07-21) on location **`eu`** (multi-region).
  Its model page lists `eu` as the only European location: no single EU region.
- Embeddings: **`gemini-embedding-2`** on `eu`. Probed live on 2026-10-27
  (`tools/check_vertex.py`): on `eu` only `gemini-embedding-2` answers;
  `gemini-embedding-001` and `text-multilingual-embedding-002` return 404 there and
  answer only on single regions (`europe-west1`, `-west4`, `-west9`), where
  `gemini-embedding-2` returns 404. The locations page lists all of them everywhere.
- BigQuery dataset: **`EU`** multi-region, the same geography.
- Cloud Run, Artifact Registry, Cloud Storage: **`europe-west1`** (Belgium).

## Alternatives rejected

- **`europe-west9` (Paris) for Gemini.** The generic locations page lists it, but
  the Flash-Lite model page does not. The model page wins.
- **`global` endpoint.** Best availability, but no EU processing guarantee.
- **`us-central1`.** Default in every sample; data would leave the EU.

## Consequences

- One Vertex client, `location="eu"`, for both generation and embeddings.
- Lesson: check model availability with a live call, not only the docs.
- `eu` endpoints do not guarantee in-region ML processing on their own; the data
  residency page is the reference if the question comes up.
