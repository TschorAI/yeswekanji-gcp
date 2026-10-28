#!/usr/bin/env bash
# Create the Cloud Run service account and grant it least-privilege roles.
# Reads: config.env (PROJECT_ID, BQ_DATASET, BQ_LOCATION, AUDIO_BUCKET, RUN_SA_NAME).
# Writes: service account, IAM bindings on project, dataset, two tables, bucket. Idempotent.
source "$(dirname "$0")/lib.sh"
SA="$RUN_SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
M="serviceAccount:$SA"

step "service account $SA"
if gcloud iam service-accounts describe "$SA" >/dev/null 2>&1; then ok "exists"
else gcloud iam service-accounts create "$RUN_SA_NAME" --display-name="$RUN_SA_NAME (Cloud Run)"; fi

step "project roles: run BigQuery jobs, call Vertex AI"
for role in roles/bigquery.jobUser roles/aiplatform.user; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="$M" --role="$role" --condition=None >/dev/null
  ok "$role"
done

step "BigQuery: read the dataset, write reviews and themes only"
# --location: GRANT reads no table, so without it the job runs in US and the dataset is "Not found".
bq query --location="$BQ_LOCATION" --use_legacy_sql=false "
GRANT \`roles/bigquery.dataViewer\` ON SCHEMA \`$PROJECT_ID.$BQ_DATASET\` TO '$M';
GRANT \`roles/bigquery.dataEditor\` ON TABLE \`$PROJECT_ID.$BQ_DATASET.reviews\` TO '$M';
GRANT \`roles/bigquery.dataEditor\` ON TABLE \`$PROJECT_ID.$BQ_DATASET.themes\` TO '$M'"

step "bucket: read and create objects, no delete"
for role in roles/storage.objectViewer roles/storage.objectCreator; do
  gcloud storage buckets add-iam-policy-binding "gs://$AUDIO_BUCKET" --member="$M" --role="$role" >/dev/null
  ok "$role"
done
