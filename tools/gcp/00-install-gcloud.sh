#!/usr/bin/env bash
# Install the Google Cloud CLI (gcloud, bq, gsutil) on Ubuntu/Debian from Google's apt repo,
# then log the CLI in. Reads: nothing. Writes: apt sources, /usr/share/keyrings, ~/.config/gcloud.
# Idempotent: skips what is already done.
set -euo pipefail

if command -v gcloud >/dev/null; then
  echo "   ok: gcloud already installed ($(gcloud --version | head -1))"
else
  sudo apt-get install -y apt-transport-https ca-certificates gnupg curl
  curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
    | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
  sudo apt-get update && sudo apt-get install -y google-cloud-cli
fi

# CLI identity (browser). Python uses a separate login: Application Default Credentials.
if [ -n "$(gcloud auth list --filter=status:ACTIVE --format='value(account)')" ]; then
  echo "   ok: logged in as $(gcloud auth list --filter=status:ACTIVE --format='value(account)')"
else
  gcloud auth login
fi
