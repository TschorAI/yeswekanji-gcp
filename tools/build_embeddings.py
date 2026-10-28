"""Embed every kanji entry with Vertex AI and load the vectors into BigQuery.

Reads: BigQuery kanji (via src/bq_data.py), tools/gcp/config.env (VERTEX_LOCATION).
Writes: data/embeddings.ndjson (cache: a rerun only embeds what is missing),
BigQuery table kanji_embeddings (replaced).
Cost: about 2,000 calls of ~30 tokens, well under one cent.

gemini-embedding-2 merges a list of inputs into ONE vector without error,
so this sends one text per call, in parallel, and checks each result.
"""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from google import genai
from google.cloud import bigquery
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import bq_data  # noqa: E402
from cards import clean_kana  # noqa: E402

MODEL = "gemini-embedding-2"
DIM = 768
CACHE = ROOT / "data" / "embeddings.ndjson"
WORKERS = 8


def entry_text(k: dict) -> str:
    """What gets embedded: character, French and English meanings, readings."""
    fr = "; ".join(k["meanings_fr"])
    en = "; ".join(k["meanings_en"])
    readings = ", ".join([clean_kana(r) for r in k["kun"]] + k["on"])
    return f"{k['literal']}: {fr} / {en} ({readings})"


def embed_one(client: genai.Client, text: str) -> list[float]:
    r = client.models.embed_content(
        model=MODEL,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=DIM, task_type="RETRIEVAL_DOCUMENT"),
    )
    assert len(r.embeddings) == 1 and len(r.embeddings[0].values) == DIM
    return r.embeddings[0].values


def main() -> None:
    client = genai.Client(
        vertexai=True,
        project=bq_data.PROJECT,
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "eu"),
    )
    kanji = bq_data.load_kanji()

    cached: dict[str, dict] = {}
    if CACHE.exists():
        for line in CACHE.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row["model"] == MODEL:
                cached[row["literal"]] = row
    todo = [k for lit, k in kanji.items() if lit not in cached]
    print(f"{len(kanji)} kanji, {len(cached)} cached, embedding {len(todo)}")

    def work(k: dict) -> dict:
        text = entry_text(k)
        return {"literal": k["literal"], "text": text, "model": MODEL, "embedding": embed_one(client, text)}

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(WORKERS) as pool, CACHE.open("a", encoding="utf-8") as f:
        for i, row in enumerate(pool.map(work, todo), 1):
            cached[row["literal"]] = row
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            if i % 200 == 0:
                print(f"  {i}/{len(todo)}")

    rows = [cached[lit] for lit in kanji]
    schema = [
        bigquery.SchemaField("literal", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("text", "STRING"),
        bigquery.SchemaField("model", "STRING"),
        bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
    ]
    job = bq_data.client().load_table_from_json(
        rows,
        f"{bq_data.PROJECT}.{bq_data.DATASET}.kanji_embeddings",
        job_config=bigquery.LoadJobConfig(schema=schema, write_disposition="WRITE_TRUNCATE"),
    )
    job.result()
    print(f"kanji_embeddings: {job.output_rows} rows loaded")


if __name__ == "__main__":
    main()
