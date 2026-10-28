"""Demo of the BigQuery data layer from Python, with dry-run costs.

Reads: BigQuery kanji, themes, reviews. Writes: one test row in reviews (user_id 'demo').
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import bq_data  # noqa: E402


def main() -> None:
    bq = bq_data.client()
    for sql in [
        f"SELECT * FROM {bq_data.table('kanji')}",
        f"SELECT {bq_data.KANJI_COLUMNS} FROM {bq_data.table('kanji')}",
        f"SELECT literal FROM {bq_data.table('kanji')}",
    ]:
        print(f"{bq_data.dry_run_bytes(sql, bq):>8} bytes  {sql[:70]}")

    kanji = bq_data.load_kanji(bq)
    themes = bq_data.load_themes(bq)
    print(f"\nloaded {len(kanji)} kanji, {len(themes)} themes")
    print("水 ->", kanji["水"]["meanings_fr"], kanji["水"]["kun"])

    bq_data.log_review("demo", "水", "nature", bq)
    rows = bq.query(
        f"SELECT ts, user_id, literal FROM {bq_data.table('reviews')} "
        "WHERE ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY) ORDER BY ts DESC LIMIT 3"
    ).result()
    print("\nlatest reviews:")
    for r in rows:
        print(" ", r["ts"], r["user_id"], r["literal"])


if __name__ == "__main__":
    main()
