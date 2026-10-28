# ADR 0005: Audio: Cloud Text-to-Speech, all MP3s in a private Cloud Storage bucket

Date: 2026-10-28. Status: Accepted. Supersedes source ADR 0003 for generated themes.

## Context

The 100 curated MP3s were pre-generated with gTTS (source ADR 0003). Themes generated
on the fly (ADR 0002) need audio at runtime. Cloud Run's file system is in memory and
lost on every restart or new instance.

## Decision

- **Voice:** Cloud Text-to-Speech, `fr-FR-Neural2-*` then `ja-JP-Neural2-*`, MP3 at
  24 kHz. The French clip ends with an SSML `<break time="600ms"/>`; the two MP3s are
  joined by byte concatenation (same encoder and rate), as the source app did.
- **Storage:** one private bucket in `europe-west1`, `audio/u<hex>.mp3`, the source
  app's naming. The 100 curated files are uploaded once. A missing file is generated,
  uploaded, then served: each kanji is synthesised once, ever.
- **Serving:** the app reads the object with its service account and passes the bytes
  to `st.audio`. The bucket is never public.

## Alternatives rejected

- **MP3s in the container.** Fine for the 100 fixed files, but generated files would
  vanish on restart, and every new file would need an image rebuild.
- **gTTS at runtime.** Unofficial endpoint, rate-limited, no SLA, no IAM.
- **Public bucket, browser fetches the URL.** Less app traffic, but public objects
  and `allUsers` grants; signed URLs need extra IAM (token creator). Not worth it here.
- **Two places (container for curated, bucket for generated).** Two code paths.

## Consequences

- One more API (`texttospeech`) and one more role on the service account
  (object read/write on this bucket only).
- Cost: about 20 characters per kanji; a theme is ~200 characters, inside any free tier.
