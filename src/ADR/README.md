# Architecture Decision Records

One decision per file, numbered, never edited after acceptance. A superseded ADR
gets a "Superseded by" line and stays. Format: Context, Decision, Alternatives
rejected, Consequences.

Decisions inherited from the source app (KANJIDIC2, curated themes, gTTS, French
from KANJIDIC2, audio playback) are in [yeswekanji](https://github.com/TschorAI/yeswekanji)
(`ADR/`) and still hold unless superseded here. This version runs on Google Cloud
and adds one feature: themes generated on the fly.

| # | Decision | Status |
|---|---|---|
| [0001](0001-regions-eu.md) | Regions: BigQuery `EU`, Vertex AI `eu`, Cloud Run `europe-west1` | Accepted |
| [0002](0002-genai-feature-theme-generator.md) | GenAI feature: generate a lexical field on the fly | Accepted |
| [0003](0003-vectors-in-bigquery.md) | Store and search embeddings in BigQuery | Accepted |
| [0004](0004-theme-check-and-expansion.md) | Step 0 checks and expands the theme; k = 30 | Accepted |
| [0005](0005-audio-cloud-tts-gcs.md) | Audio: Cloud TTS, MP3s in a private bucket | Accepted |
