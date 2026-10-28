#!/usr/bin/env bash
# Deploy the image to Cloud Run as the least-privilege service account.
# Reads: config.env. Usage: 07-deploy.sh <image tag>. Writes: Cloud Run service $RUN_SERVICE.
# Public URL (--allow-unauthenticated); spend bounded by DAILY_THEME_CAP and --max-instances.
source "$(dirname "$0")/lib.sh"
TAG="${1:?usage: 07-deploy.sh <image tag>}"
IMAGE="$RUN_REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/$IMAGE_NAME:$TAG"

step "deploy $RUN_SERVICE <- $IMAGE"
gcloud run deploy "$RUN_SERVICE" --image="$IMAGE" --region="$RUN_REGION" \
  --service-account="$RUN_SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --allow-unauthenticated --session-affinity --timeout=3600 \
  --cpu=1 --memory=1Gi --min-instances=0 --max-instances=2 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,BQ_DATASET=$BQ_DATASET,AUDIO_BUCKET=$AUDIO_BUCKET,GOOGLE_CLOUD_LOCATION=$VERTEX_LOCATION,DAILY_THEME_CAP=$DAILY_THEME_CAP"
