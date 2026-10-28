"""BigQuery data layer: replaces cards.load_kanji / load_themes, logs card flips.

Reads: BigQuery tables kanji, themes. Writes: BigQuery table reviews.
Config from env vars (GOOGLE_CLOUD_PROJECT, BQ_DATASET), so Cloud Run sets them without a file.
Credentials: ADC (your login locally, the service account on Cloud Run).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from google.cloud import bigquery

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "yeswekanji-gcp-deploy")
DATASET = os.environ.get("BQ_DATASET", "kanji")
KANJI_COLUMNS = (
    "literal, grade, jlpt, freq, stroke_count, `on`, kun, "
    "romaji_on, romaji_kun, meanings_en, meanings_fr"
)


def client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT)


def table(name: str) -> str:
    return f"`{PROJECT}.{DATASET}.{name}`"


def dry_run_bytes(sql: str, bq: bigquery.Client | None = None) -> int:
    """Bytes the query would scan, without running it or paying for it."""
    bq = bq or client()
    job = bq.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
    return job.total_bytes_processed


def load_kanji(bq: bigquery.Client | None = None) -> dict[str, dict]:
    """Same shape as cards.load_kanji(): {literal: entry}. Call once and cache it."""
    bq = bq or client()
    rows = bq.query(f"SELECT {KANJI_COLUMNS} FROM {table('kanji')}").result()
    return {r["literal"]: dict(r.items()) for r in rows}


def load_themes(bq: bigquery.Client | None = None) -> list[dict]:
    """Same shape as cards.load_themes(): curated first, then generated, by name."""
    bq = bq or client()
    sql = f"SELECT id, name_fr, name_en, kanji, source FROM {table('themes')} ORDER BY source, name_fr"
    return [dict(r.items()) for r in bq.query(sql).result()]


def generated_today(bq: bigquery.Client | None = None) -> int:
    """Themes generated since midnight UTC, for the daily cap."""
    bq = bq or client()
    sql = (f"SELECT COUNT(*) AS n FROM {table('themes')} "
           "WHERE source = 'generated' AND created_at >= TIMESTAMP(CURRENT_DATE())")
    return next(iter(bq.query(sql).result()))["n"]


def log_review(user_id: str, literal: str, theme_id: str | None, bq: bigquery.Client | None = None) -> None:
    """Append one card flip. Streaming insert: visible to queries within seconds."""
    bq = bq or client()
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "literal": literal,
        "theme_id": theme_id,
    }
    errors = bq.insert_rows_json(f"{PROJECT}.{DATASET}.reviews", [row])
    if errors:
        raise RuntimeError(f"reviews insert failed: {errors}")
