"""Convert the app's JSON files to newline-delimited JSON, the format `bq load` reads.

Reads: data/kanji.json (dict keyed by literal), data/themes.json (list).
Writes: data/bq/kanji.ndjson, data/bq/themes.ndjson (one object per line).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "bq"


def write_ndjson(rows: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{path.relative_to(ROOT)}: {len(rows)} rows")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    kanji = json.loads((DATA / "kanji.json").read_text(encoding="utf-8"))
    write_ndjson(list(kanji.values()), OUT / "kanji.ndjson")
    themes = json.loads((DATA / "themes.json").read_text(encoding="utf-8"))
    for t in themes:
        t["source"] = "curated"
    write_ndjson(themes, OUT / "themes.ndjson")


if __name__ == "__main__":
    main()
