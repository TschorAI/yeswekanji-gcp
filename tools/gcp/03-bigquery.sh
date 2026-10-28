#!/usr/bin/env bash
# Create the BigQuery dataset and tables, load kanji and themes.
# Reads: config.env (PROJECT_ID, BQ_LOCATION, BQ_DATASET), data/bq/*.ndjson (tools/to_ndjson.py),
# src/bq/*.schema.json. Writes: BigQuery dataset and tables. Batch loads are free.
source "$(dirname "$0")/lib.sh"
ROOT="$(cd "$GCP_DIR/../.." && pwd)"
DS="$PROJECT_ID:$BQ_DATASET"

step "dataset $DS ($BQ_LOCATION)"
if bq show "$DS" >/dev/null 2>&1; then ok "exists"
else bq --location="$BQ_LOCATION" mk --dataset --description="yeswekanji kanji app" "$DS"; fi

# --replace: bq load appends by default, so a second run would duplicate every row.
for t in kanji themes; do
  step "load $t"
  bq load --replace --source_format=NEWLINE_DELIMITED_JSON \
    "$DS.$t" "$ROOT/data/bq/$t.ndjson" "$ROOT/src/bq/$t.schema.json"
done

step "reviews (partitioned by day on ts, clustered by user_id)"
if bq show "$DS.reviews" >/dev/null 2>&1; then ok "exists, never replaced: it holds the log"
else bq mk --table --time_partitioning_field=ts --time_partitioning_type=DAY \
  --clustering_fields=user_id "$DS.reviews" "$ROOT/src/bq/reviews.schema.json"; fi
