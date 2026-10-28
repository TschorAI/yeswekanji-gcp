# yeswekanji-gcp

## Summary

- **What:** Live demo: https://yeswekanji.leonardtschora.com. Yes we kanji, an app to learn Japanese kanji with flip cards and audio, on Google Cloud. Type any theme and get ten matching kanji (Gemini + RAG over KANJIDIC2).
- **Status:** in progress
- **Created by:** leonardtschora
- **Created on:** 2026-10-27
- **Repository:** https://github.com/leonardtschora/yeswekanji-gcp
- **Shared drive and tasks:** personal project, own drive · task board https://github.com/users/leonardtschora/projects/17

## Index

| Folder | Holds | Stored in |
|---|---|---|
| `sources/` | Background and seed documents, as received | Own drive |
| `data/` | Input and intermediate data, pulled or computed | Own drive |
| `src/` | Document sources, working notes, and the code that turns `data/` into `out/` | GitHub |
| `tools/` | Scripts that fetch, convert or clean into `data/`; checkers and linters | GitHub |
| `out/reports/` | Compiled documents: PDFs, presentations | Own drive |
| `out/figures/` | Generated images | Own drive |
| `out/videos/` | Generated videos | Own drive |
| `out/data/` | Computed results: predictions, result tables | Own drive |
| `tasks/` | One file per task | Own drive + task board |

### Documents and code (`src/` -> `out/`)

- `src/app.py`, `src/cards.py`: the Streamlit app, copied from yeswekanji, being ported.
- `Dockerfile`, `.dockerignore`, `.gcloudignore`: the Cloud Run image (runtime deps and `src/` only).
- `src/ADR/`: one file per decision.
- `src/bq_data.py`: BigQuery data layer for the app: load kanji and themes, log card flips to `reviews`, dry-run costs.
- `src/theme_gen.py`: feature C, a lexical field generated on the fly (retrieve with `VECTOR_SEARCH`, Gemini picks 10 or refuses, validation).
- `src/eval_themes.py`, `src/eval/gold_themes.json`: 10-theme test set for feature C; writes `out/data/eval_themes.csv`.
- `src/audio.py`: card audio from the private bucket; a missing MP3 is synthesised once with Cloud TTS and uploaded.
- `src/bq/*.schema.json`: BigQuery table schemas (kanji, themes, reviews).

### Tools

- `tests/test_offline.py`: offline tests (helpers, eval scoring), run by `.github/workflows/ci.yml`.
- `tools/gcp/`: re-runnable GCP setup scripts `00`-`07`, one per step, plus `99-teardown.sh` (destructive), configured by `tools/gcp/config.env` (copy `config.example`; gitignored).
- `tools/to_ndjson.py`: converts `data/kanji.json` and `data/themes.json` to `data/bq/*.ndjson` for `bq load`.
- `tools/demo_bq.py`: demo of `src/bq_data.py`: dry-run costs, loads, one test row (user `demo`) in `reviews`.
- `tools/build_embeddings.py`: embeds the 1987 kanji entries (gemini-embedding-2, 768 dims) into BigQuery `kanji_embeddings`; cache in `data/embeddings.ndjson`.
- `tools/diagram_gcp.py`: draws the GCP architecture (services, request and build paths, step numbers, IAM) to `out/figures/gcp_architecture.png` and `.pdf`.
- `tools/check_vertex.py`: smoke test, one Gemini call and one embedding call on the configured Vertex location.

### Sources and data

- `data/kanji.json`, `data/themes.json`, `data/audio/`: copied from yeswekanji (KANJIDIC2 extract, CC BY-SA 4.0; 1987 kanji, 100 MP3s).

## Run it

Locally, against your own GCP project (scripts in `tools/gcp/`, configured by `tools/gcp/config.env`, copied from `config.example`):

    bash tools/gcp/00-install-gcloud.sh      # then 01 to 05: project, billing, APIs, BigQuery, bucket, service account
    uv sync
    uv run python tools/to_ndjson.py && bash tools/gcp/03-bigquery.sh
    uv run python tools/build_embeddings.py
    uv run streamlit run src/app.py          # http://localhost:8501
    bash tools/gcp/06-build.sh v1 && bash tools/gcp/07-deploy.sh v1   # Cloud Run

Tests, offline: `uv run --group test pytest`. Teardown: `bash tools/gcp/99-teardown.sh`.

## How this was built

A port of [yeswekanji](https://github.com/TschorAI/yeswekanji), a Streamlit kanji-flashcard app
that read committed JSON and MP3 files, to Google Cloud, with one new feature: themes generated on
the fly. The infrastructure was set up by hand with `gcloud` and `bq`, then saved as the scripts in
`tools/gcp/`; the Python was written with Claude Code (Anthropic) as coding assistant.

- **Data in BigQuery** (dataset `EU`): the 1,987 KANJIDIC2 entries, the themes, and a `reviews` log
  partitioned by day. The cost model (bytes in the columns touched) was measured with dry runs.
- **A theme generator (RAG):** Gemini checks the request and expands it, `gemini-embedding-2` embeds it,
  BigQuery `VECTOR_SEARCH` returns 30 candidates, Gemini picks 10 as JSON, code rejects anything outside
  the candidates. A 10-theme test set, 3 runs each, went from 21/30 to 30/30 with the check step
  (ADR 0004); the retriever was the bottleneck.
- **Audio:** Cloud Text-to-Speech, each MP3 made once and kept in a private Cloud Storage bucket.
- **Cloud Run** behind a least-privilege service account, image built by Cloud Build into Artifact
  Registry. No API key anywhere.

Decisions and the alternatives rejected: `src/ADR/`. Things the docs got wrong, found with live
calls: Flash-Lite is only on the `eu` multi-region; on `eu` only `gemini-embedding-2` answers, and it
merges a list of inputs into one vector without error; `google-genai` has no default HTTP timeout;
BigQuery refuses a vector index under 5,000 rows.

More projects: [leonardtschora.com](https://leonardtschora.com).
