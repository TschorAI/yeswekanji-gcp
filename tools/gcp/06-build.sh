#!/usr/bin/env bash
# Create the Artifact Registry repo, build the image with Cloud Build, push it there.
# Reads: config.env (PROJECT_ID, RUN_REGION, AR_REPO, IMAGE_NAME), Dockerfile, .gcloudignore.
# Writes: repo $AR_REPO, image $RUN_REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/$IMAGE_NAME:<tag>.
# Usage: 06-build.sh [tag]   (default tag: date-time). Costs: a few build minutes, free tier.
source "$(dirname "$0")/lib.sh"
ROOT="$(cd "$GCP_DIR/../.." && pwd)"
TAG="${1:-$(date +%Y%m%d-%H%M)}"
IMAGE="$RUN_REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/$IMAGE_NAME:$TAG"

step "Artifact Registry repo $AR_REPO ($RUN_REGION)"
if gcloud artifacts repositories describe "$AR_REPO" --location="$RUN_REGION" >/dev/null 2>&1; then ok "exists"
else gcloud artifacts repositories create "$AR_REPO" --repository-format=docker \
  --location="$RUN_REGION" --description="yeswekanji images"; fi

step "Cloud Build -> $IMAGE"
gcloud builds submit "$ROOT" --region="$RUN_REGION" --tag="$IMAGE"
echo "$IMAGE"
