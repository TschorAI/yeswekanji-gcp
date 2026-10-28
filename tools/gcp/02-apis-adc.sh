#!/usr/bin/env bash
# Enable the project's APIs and set up Application Default Credentials for Python.
# Reads: config.env (PROJECT_ID). Writes: enabled services, ~/.config/gcloud/application_default_credentials.json.
# Enabling an API is free; only usage is billed.
source "$(dirname "$0")/lib.sh"

step "APIs"
gcloud services enable --project="$PROJECT_ID" \
  bigquery.googleapis.com aiplatform.googleapis.com \
  run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com \
  storage.googleapis.com texttospeech.googleapis.com iam.googleapis.com

step "ADC (libraries' identity, separate from the CLI login)"
if gcloud auth application-default print-access-token >/dev/null 2>&1; then ok "present"
else gcloud auth application-default login; fi
gcloud auth application-default set-quota-project "$PROJECT_ID"
