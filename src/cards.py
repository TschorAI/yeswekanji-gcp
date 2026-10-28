"""Data helpers shared by app.py and tools/build_audio.py.

Pure Python, no Streamlit import, so scripts and tests can use it.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
KANJI_PATH = DATA / "kanji.json"
THEMES_PATH = DATA / "themes.json"
AUDIO_DIR = DATA / "audio"


def load_kanji() -> dict[str, dict]:
    return json.loads(KANJI_PATH.read_text(encoding="utf-8"))


def load_themes() -> list[dict]:
    return json.loads(THEMES_PATH.read_text(encoding="utf-8"))


def clean_kana(reading: str) -> str:
    """Drop KANJIDIC2's suffix marker '-' and okurigana marker '.'."""
    return reading.replace("-", "").replace(".", "")


def french_meanings(k: dict, n: int = 2) -> list[str]:
    """First n French meanings, skipping KANJIDIC2's 'radical X (no. N)' notes."""
    fr = [m for m in k["meanings_fr"] if not m.lower().startswith("radical ")]
    return (fr or k["meanings_fr"])[:n]


def french_label(k: dict) -> str:
    return ", ".join(french_meanings(k))


def spoken_reading(k: dict) -> str:
    """Kana read aloud: first kun reading cleaned, else first on reading."""
    if k["kun"]:
        return clean_kana(k["kun"][0])
    return k["on"][0]


def _dedup(items: list[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        if item and item not in out:
            out.append(item)
    return out


def romaji_line(k: dict, max_kun: int = 3, max_on: int = 2) -> str:
    """Kun romaji first, then on romaji, de-duplicated, capped for the card."""
    kun = _dedup(k["romaji_kun"])[:max_kun]
    on = _dedup(k["romaji_on"])[:max_on]
    return ", ".join(_dedup(kun + on))


def kana_line(k: dict, max_kun: int = 3, max_on: int = 2) -> str:
    """Same readings as romaji_line, in kana (markers removed)."""
    kun = _dedup([clean_kana(r) for r in k["kun"]])[:max_kun]
    on = _dedup(k["on"])[:max_on]
    return "・".join(kun + on)


def audio_path(literal: str) -> Path:
    """data/audio/u65e5.mp3 for 日: file names by code point, ASCII only."""
    return AUDIO_DIR / f"u{ord(literal):04x}.mp3"
