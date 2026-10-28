#!/usr/bin/env bash
# Delete everything this project created, so nothing keeps billing. DESTRUCTIVE, not idempotent.
# Reads: config.env. Usage: 99-teardown.sh [--project]  (--project: delete the whole project instead).
source "$(dirname "$0")/lib.sh"
read -r -p "Delete all resources of $PROJECT_ID? Type the project id to confirm: " answer
[ "$answer" = "$PROJECT_ID" ] || { echo "aborted"; exit 1; }

if [ "${1:-}" = "--project" ]; then
  # Shuts down every resource and stops billing at once; recoverable for 30 days.
  gcloud projects delete "$PROJECT_ID"
  exit 0
fi
gcloud run services delete "$RUN_SERVICE" --region="$RUN_REGION" --quiet
gcloud artifacts repositories delete "$AR_REPO" --location="$RUN_REGION" --quiet
gcloud storage rm --recursive "gs://$AUDIO_BUCKET"
gcloud storage rm --recursive "gs://${PROJECT_ID}_cloudbuild" || true   # build sources
bq rm -r -f -d "$PROJECT_ID:$BQ_DATASET"
gcloud iam service-accounts delete "$RUN_SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" --quiet
echo "budget left in place (free). Delete it in Billing > Budgets if wanted."
