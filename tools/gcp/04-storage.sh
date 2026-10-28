#!/usr/bin/env bash
# Create the private audio bucket and upload the curated MP3s (src/ADR/0005).
# Reads: config.env (PROJECT_ID, RUN_REGION, AUDIO_BUCKET), data/audio/*.mp3.
# Writes: bucket gs://$AUDIO_BUCKET, objects audio/u<hex>.mp3. Idempotent.
source "$(dirname "$0")/lib.sh"
ROOT="$(cd "$GCP_DIR/../.." && pwd)"

step "bucket gs://$AUDIO_BUCKET ($RUN_REGION, private)"
if gcloud storage buckets describe "gs://$AUDIO_BUCKET" >/dev/null 2>&1; then ok "exists"
else gcloud storage buckets create "gs://$AUDIO_BUCKET" --project="$PROJECT_ID" \
  --location="$RUN_REGION" --uniform-bucket-level-access --public-access-prevention; fi

step "upload curated MP3s"
# --no-clobber: skip objects already there, so a rerun never overwrites generated audio.
gcloud storage cp --no-clobber "$ROOT"/data/audio/*.mp3 "gs://$AUDIO_BUCKET/audio/"
ok "$(gcloud storage ls "gs://$AUDIO_BUCKET/audio/" | wc -l) objects"
