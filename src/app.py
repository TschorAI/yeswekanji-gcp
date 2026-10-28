"""Yes we kanji on GCP: ten kanji cards from one lexical field, curated or generated. Click to flip.

Run:  uv run streamlit run src/app.py
Data: BigQuery (bq_data). Audio: Cloud Storage + Cloud TTS (audio). New themes: theme_gen.
Each flip is logged to BigQuery reviews. Decisions: src/ADR/, source app ADR 0006 (autoplay).
Config from env vars: GOOGLE_CLOUD_PROJECT, BQ_DATASET, AUDIO_BUCKET, GOOGLE_CLOUD_LOCATION,
DAILY_THEME_CAP.
"""

from __future__ import annotations

import html
import logging
import os
import random
import uuid

import streamlit as st

import audio
import bq_data
import cards
import theme_gen

log = logging.getLogger("yeswekanji")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
DAILY_THEME_CAP = int(os.environ.get("DAILY_THEME_CAP", "20"))

st.set_page_config(page_title="Yes we kanji", page_icon="漢", layout="wide")

COLUMNS = 5

CSS = """
<style>
.st-key-grid div.stButton button {
    min-height: 13rem;
    border-radius: 0.8rem;
}
.st-key-grid div.stButton button p {
    font-size: 4.5rem;
    line-height: 1.1;
}
.ywk-card { text-align: center; min-height: 11rem; display: flex;
    flex-direction: column; justify-content: center; gap: 0.25rem; }
.ywk-kanji { font-size: 3.2rem; line-height: 1.1; }
.ywk-romaji { font-size: 1.05rem; font-weight: 600; }
.ywk-fr { font-size: 1.1rem; }
.ywk-kana { font-size: 0.85rem; opacity: 0.55; }
</style>
"""


@st.cache_resource
def clients():
    """One BigQuery and one Vertex client per process, shared by all sessions."""
    return bq_data.client(), theme_gen.vertex()


@st.cache_data
def get_kanji() -> dict[str, dict]:
    return bq_data.load_kanji(clients()[0])


@st.cache_data(ttl=300)
def get_themes() -> list[dict]:
    return bq_data.load_themes(clients()[0])


@st.cache_data(max_entries=200)
def get_audio(literal: str) -> bytes:
    mp3, generated = audio.get_audio(get_kanji()[literal])
    if generated:
        log.info("audio generated literal=%s", literal)
    return mp3


def new_draw() -> None:
    """Hide every card again and shuffle the order of the current theme."""
    st.session_state.flipped = {}
    st.session_state.last_flipped = None
    st.session_state.order_seed = random.random()


def flip(literal: str) -> None:
    st.session_state.flipped[literal] = True
    st.session_state.last_flipped = literal
    try:
        bq_data.log_review(st.session_state.user_id, literal, st.session_state.theme_id, clients()[0])
    except Exception:  # a lost log line must never break the card
        log.exception("review log failed literal=%s", literal)


def new_theme() -> None:
    """Callback of the "Nouveau thème" form: check, retrieve, select, validate, save."""
    text = st.session_state.new_theme_text.strip()
    if not text:
        return
    bq, ai = clients()
    if bq_data.generated_today(bq) >= DAILY_THEME_CAP:
        st.session_state.gen_msg = ("warning", f"Limite de {DAILY_THEME_CAP} thèmes générés par jour atteinte.")
        return
    res = theme_gen.generate(text, ai, bq)
    log.info("theme generated text=%r refused=%s at=%s tokens=%s", text, res.refused, res.refused_at, res.tokens)
    if res.refused:
        st.session_state.gen_msg = ("error", f"Thème refusé : {res.reason}")
        return
    row = theme_gen.save_theme(res, bq)
    get_themes.clear()
    st.session_state.theme_id = row["id"]
    st.session_state.setdefault("gen_reasons", {})[row["id"]] = {p.literal: p.reason_fr for p in res.picks}
    st.session_state.gen_msg = ("success", f"Nouveau thème : {res.name_fr}")
    new_draw()


def card_html(k: dict) -> str:
    e = html.escape
    return (
        '<div class="ywk-card">'
        f'<div class="ywk-kanji">{e(k["literal"])}</div>'
        f'<div class="ywk-romaji">{e(cards.romaji_line(k))}</div>'
        f'<div class="ywk-fr">{e(", ".join(cards.french_meanings(k)))}</div>'
        f'<div class="ywk-kana">{e(cards.kana_line(k))}</div>'
        "</div>"
    )


def main() -> None:
    kanji = get_kanji()
    themes = {t["id"]: t for t in get_themes()}

    if "user_id" not in st.session_state:
        st.session_state.user_id = uuid.uuid4().hex[:12]
    if "theme_id" not in st.session_state:
        curated = [tid for tid, t in themes.items() if t.get("source") == "curated"]
        st.session_state.theme_id = random.choice(curated or list(themes))
        new_draw()

    st.markdown(CSS, unsafe_allow_html=True)
    st.title("Yes we kanji")

    pick, reset = st.columns([3, 1], vertical_alignment="bottom")
    with pick:
        st.selectbox(
            "Thème",
            options=list(themes),
            format_func=lambda tid: themes[tid]["name_fr"] + (" ✦" if themes[tid].get("source") == "generated" else ""),
            key="theme_id",
            on_change=new_draw,
        )
    with reset:
        st.button("Nouveau tirage", on_click=new_draw, width="stretch")

    with st.form("gen", clear_on_submit=True, border=False):
        text_col, go_col = st.columns([3, 1], vertical_alignment="bottom")
        text_col.text_input("Nouveau thème", key="new_theme_text", placeholder="ex. la cuisine, la météo, les émotions")
        go_col.form_submit_button("Générer", on_click=new_theme, width="stretch")
    if msg := st.session_state.pop("gen_msg", None):
        getattr(st, msg[0])(msg[1])

    theme = themes[st.session_state.theme_id]
    order = list(theme["kanji"])
    random.Random(st.session_state.order_seed).shuffle(order)
    st.caption(f"{theme['name_fr']} · {theme['name_en']} — cliquez sur une carte pour la retourner.")

    to_play = st.session_state.last_flipped
    with st.container(key="grid"):
        for start in range(0, len(order), COLUMNS):
            for col, literal in zip(st.columns(COLUMNS), order[start : start + COLUMNS]):
                with col:
                    if not st.session_state.flipped.get(literal):
                        st.button(literal, key=f"card_{literal}", on_click=flip, args=(literal,), width="stretch")
                        continue
                    with st.container(border=True):
                        st.markdown(card_html(kanji[literal]), unsafe_allow_html=True)
                        if literal == to_play:
                            # Rendered for the card just flipped only, once: avoids the
                            # duplicate-widget error (streamlit#11360). The visible player
                            # stays as a fallback where autoplay is blocked (iOS Safari).
                            st.audio(get_audio(literal), format="audio/mp3", autoplay=True)
                        if reason := st.session_state.get("gen_reasons", {}).get(theme["id"], {}).get(literal):
                            st.caption(reason)
    st.session_state.last_flipped = None

    with st.expander("À propos"):
        st.markdown(
            "Données kanji : fichier [KANJIDIC2](https://www.edrdg.org/wiki/index.php/KANJIDIC_Project), "
            "propriété de l'Electronic Dictionary Research and Development Group (EDRDG), utilisé "
            "conformément à la [licence du groupe](https://www.edrdg.org/edrdg/licence.html) "
            "(Creative Commons Attribution-ShareAlike 4.0). Significations françaises de "
            "KANJIDIC2 (Alain Thierion).\n\n"
            "Voix : thèmes d'origine générés à l'avance avec [gTTS](https://github.com/pndurette/gTTS) ; "
            "nouveaux thèmes avec Google Cloud Text-to-Speech.\n\n"
            "Thèmes générés (✦) : choisis par Gemini parmi les kanji les plus proches dans KANJIDIC2.\n\n"
            "Romaji : [pykakasi](https://codeberg.org/miurahr/pykakasi), transcription Hepburn."
        )


main()
