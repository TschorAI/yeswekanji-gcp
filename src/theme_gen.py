"""Feature C: generate a lexical field on the fly (src/ADR/0002, 0004).

0 Check: Gemini decides whether the input is a theme, and expands it with related words.
1 Retrieve: embed the expanded theme, VECTOR_SEARCH the nearest kanji in BigQuery.
2 Select: Gemini picks 10 of the candidates as JSON, or refuses the theme.
3 Validate: any kanji outside the candidates is dropped; fewer than 10 left = refusal.

Reads: BigQuery kanji_embeddings, Vertex AI (gemini-embedding-2, gemini-3.5-flash-lite).
Writes: BigQuery themes (save_theme).
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from google import genai
from google.cloud import bigquery
from google.genai import types
from pydantic import BaseModel

import bq_data

EMBED_MODEL = "gemini-embedding-2"
GEN_MODEL = "gemini-3.5-flash-lite"
DIM = 768
N_CANDIDATES = 30
N_CARDS = 10
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "eu")


class Check(BaseModel):
    is_theme: bool
    reason_fr: str
    expanded_fr: str


class Pick(BaseModel):
    literal: str
    reason_fr: str


class Answer(BaseModel):
    refused: bool
    refusal_reason_fr: str
    name_fr: str
    name_en: str
    picks: list[Pick]


@dataclass
class Result:
    theme: str
    refused: bool
    reason: str = ""
    name_fr: str = ""
    name_en: str = ""
    picks: list[Pick] = field(default_factory=list)
    candidates: list[str] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)
    tokens: int = 0
    expanded: str = ""
    refused_at: str = ""  # "check" | "select" | "validate"


CHECK_PROMPT = """Une application d'apprentissage des kanji reçoit cette demande de thème : « {theme} ».

Un thème est un champ lexical : un domaine de la vie, de la nature, de la société ou des idées
(ex. « la cuisine », « les émotions », « le corps »).

Ce n'est PAS un thème, refuse (is_theme=false) :
- une suite de caractères sans sens ;
- une question ou une demande d'information (un prix, une prévision, un fait, une date) ;
- une demande portant sur des données personnelles (le nom de mon chat, mon adresse...) ;
- un contenu offensant.

Si c'est un thème : expanded_fr = le thème suivi de 10 à 15 mots français simples et concrets
qui en relèvent, séparés par des virgules. Sinon : expanded_fr vide, et reason_fr explique le refus.
"""

PROMPT = """Tu aides un francophone à apprendre les kanji. Thème demandé : « {theme} ».

Voici les seuls kanji autorisés, avec leur sens tiré de KANJIDIC2 :
{candidates}

Règles :
- Choisis exactement {n} kanji de cette liste qui relèvent clairement du thème. N'invente aucun kanji.
- Pour chacun, une raison courte en français, fondée sur le sens donné.
- Si le thème n'a pas de sens, est offensant, ou si moins de {n} kanji de la liste s'y rattachent
  clairement, mets refused=true, explique pourquoi, et laisse picks vide.
- name_fr : le thème reformulé proprement en français ; name_en : en anglais.
"""


def vertex() -> genai.Client:
    # The SDK has no default timeout: a stuck request would wait forever (it hung an eval run).
    return genai.Client(vertexai=True, project=bq_data.PROJECT, location=LOCATION,
                        http_options=types.HttpOptions(timeout=60_000))


def retrieve(theme: str, ai: genai.Client, bq: bigquery.Client, k: int = N_CANDIDATES) -> list[dict]:
    """Nearest kanji entries to the theme, by cosine distance, via BigQuery VECTOR_SEARCH."""
    vec = ai.models.embed_content(
        model=EMBED_MODEL,
        contents=theme,
        config=types.EmbedContentConfig(output_dimensionality=DIM, task_type="RETRIEVAL_QUERY"),
    ).embeddings[0].values
    sql = f"""
        SELECT base.literal, base.text, distance
        FROM VECTOR_SEARCH(TABLE {bq_data.table('kanji_embeddings')}, 'embedding',
                           (SELECT @q AS embedding), top_k => {k}, distance_type => 'COSINE')
        ORDER BY distance"""
    cfg = bigquery.QueryJobConfig(query_parameters=[bigquery.ArrayQueryParameter("q", "FLOAT64", vec)])
    return [dict(r.items()) for r in bq.query(sql, job_config=cfg).result(timeout=60)]


def check(theme: str, ai: genai.Client) -> tuple[Check, int]:
    """Step 0: is it a theme? If so, the theme plus related words, to embed instead."""
    resp = ai.models.generate_content(
        model=GEN_MODEL,
        contents=CHECK_PROMPT.format(theme=theme),
        config=types.GenerateContentConfig(
            temperature=0.0, response_mime_type="application/json", response_schema=Check
        ),
    )
    return resp.parsed, resp.usage_metadata.total_token_count or 0


def generate(theme: str, ai: genai.Client | None = None, bq: bigquery.Client | None = None,
             use_check: bool = True, k: int = N_CANDIDATES) -> Result:
    ai = ai or vertex()
    bq = bq or bq_data.client()
    query, tokens = theme, 0
    if use_check:
        chk, tokens = check(theme, ai)
        if not chk.is_theme:
            return Result(theme=theme, refused=True, reason=chk.reason_fr, tokens=tokens, refused_at="check")
        query = chk.expanded_fr or theme

    cands = retrieve(query, ai, bq, k=k)
    allowed = {c["literal"] for c in cands}
    listing = "\n".join(f"- {c['text']}" for c in cands)

    resp = ai.models.generate_content(
        model=GEN_MODEL,
        contents=PROMPT.format(theme=theme, candidates=listing, n=N_CARDS),
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=Answer,
        ),
    )
    ans: Answer = resp.parsed
    res = Result(theme=theme, refused=ans.refused, reason=ans.refusal_reason_fr,
                 name_fr=ans.name_fr, name_en=ans.name_en,
                 candidates=[c["literal"] for c in cands],
                 tokens=tokens + (resp.usage_metadata.total_token_count or 0),
                 expanded=query if use_check else "")
    if ans.refused:
        res.refused_at = "select"
        return res

    seen: set[str] = set()
    for p in ans.picks:
        if p.literal in allowed and p.literal not in seen:
            res.picks.append(p)
            seen.add(p.literal)
        else:
            res.dropped.append(p.literal)
    res.picks = res.picks[:N_CARDS]
    if len(res.picks) < N_CARDS:
        res.refused = True
        res.reason = f"seulement {len(res.picks)} kanji valides sur {N_CARDS}"
        res.refused_at = "validate"
    return res


def theme_id(name_fr: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name_fr.lower()).strip("-")[:30]
    return f"gen-{slug}-{hashlib.sha1(name_fr.encode()).hexdigest()[:6]}"


def save_theme(res: Result, bq: bigquery.Client | None = None) -> dict:
    """Append the theme to BigQuery themes, source 'generated'. Returns the row."""
    bq = bq or bq_data.client()
    row = {"id": theme_id(res.name_fr), "name_fr": res.name_fr, "name_en": res.name_en,
           "kanji": [p.literal for p in res.picks], "source": "generated",
           "created_at": datetime.now(timezone.utc).isoformat()}
    errors = bq.insert_rows_json(f"{bq_data.PROJECT}.{bq_data.DATASET}.themes", [row])
    if errors:
        raise RuntimeError(f"themes insert failed: {errors}")
    return row
