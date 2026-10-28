"""Smoke test: one Gemini call and one embedding call on Vertex AI, location from config.

Reads: tools/gcp/config.env (PROJECT_ID, VERTEX_LOCATION), ADC. Writes: nothing (prints).
Costs: a few hundred tokens, well under one cent.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "tools" / "gcp" / "config.env"
GEN_MODEL = "gemini-3.5-flash-lite"
EMBED_MODEL = "gemini-embedding-2"


def read_config() -> dict[str, str]:
    pairs = re.findall(r'^(\w+)="([^"]*)"', CONFIG.read_text(), flags=re.M)
    return dict(pairs)


def main() -> int:
    cfg = read_config()
    client = genai.Client(vertexai=True, project=cfg["PROJECT_ID"], location=cfg["VERTEX_LOCATION"])
    print(f"project={cfg['PROJECT_ID']} location={cfg['VERTEX_LOCATION']}")

    r = client.models.generate_content(model=GEN_MODEL, contents="Give the meaning of the kanji 水 in 3 words.")
    print(f"{GEN_MODEL}: {r.text.strip()!r}  tokens={r.usage_metadata.total_token_count}")

    e = client.models.embed_content(
        model=EMBED_MODEL,
        contents="水: water, eau; みず, スイ",
        config=types.EmbedContentConfig(output_dimensionality=768, task_type="RETRIEVAL_DOCUMENT"),
    )
    v = e.embeddings[0].values
    print(f"{EMBED_MODEL}: dim={len(v)} first={v[:3]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
