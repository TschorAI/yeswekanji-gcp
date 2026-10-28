# ADR 0003: Store and search embeddings in BigQuery

Date: 2026-10-27. Status: Accepted.

## Context

1,987 kanji vectors (about 12 MB at 768 dims). The kanji, themes and reviews are
already in BigQuery.

## Decision

Embeddings computed in Python with `google-genai` (`gemini-embedding-2`,
768 dims, `RETRIEVAL_DOCUMENT`), loaded into `kanji_embeddings` in BigQuery,
searched with `VECTOR_SEARCH`, `COSINE`, by brute force. **No vector index**:
`CREATE VECTOR INDEX ... IVF` refuses tables under 5,000 rows (error on
2026-10-27: "Total rows 1987 is smaller than min allowed 5000"), on top of the
10 MB floor for the index to be populated. Brute force is exact and fast here.

BigQuery is not required at this size; it keeps vectors next to the data, with no extra service.

## Alternatives rejected

- **numpy in memory.** Sub-millisecond, zero cost, and the right answer for the app
  alone, even at 13,108 kanji (about 40 MB). Rejected to keep one data store and
  search in SQL next to the entries.
- **Vertex AI Vector Search.** Built for millions of vectors at low latency; overkill.
- **Vertex AI RAG Engine.** Hides retrieval behind an API; we want to tune and measure it.
- **Cloud SQL + pgvector.** An instance billed per hour for 2,000 rows.
- **Embedding in SQL (`ML.GENERATE_EMBEDDING` via a remote model).** Needs a
  BigQuery connection and its own service account; Python embeds the query at runtime anyway.

## Consequences

- Each theme query costs one BigQuery query (about 1 s, min 10 MB billed), which is fine for
  a few users and wrong for a busy public app.
