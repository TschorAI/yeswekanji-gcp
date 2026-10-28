"""Offline tests: pure helpers and the eval scoring, no GCP call.

Reads: nothing. Run: uv run --group test pytest
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import cards  # noqa: E402
import eval_themes  # noqa: E402
import theme_gen  # noqa: E402

WATER = {"literal": "水", "kun": ["みず", "みず-"], "on": ["スイ"], "romaji_kun": ["mizu"],
         "romaji_on": ["sui"], "meanings_fr": ["eau"], "meanings_en": ["water"]}


def test_readings_and_labels():
    assert cards.clean_kana("ひと.つ") == "ひとつ"
    assert cards.spoken_reading(WATER) == "みず"
    assert cards.kana_line(WATER) == "みず・スイ"
    assert cards.french_meanings({"meanings_fr": ["radical eau (no. 85)", "eau"]}) == ["eau"]
    assert cards.audio_path("水").name == "u6c34.mp3"


def test_theme_id_is_stable_and_safe():
    a = theme_gen.theme_id("La météo !")
    assert a == theme_gen.theme_id("La météo !")
    assert a.startswith("gen-la-m-t-o-") and a.isascii()


def test_score_accept_and_refuse():
    known = set("水川海湖雨雪風雲雷霧泉")
    picks = [theme_gen.Pick(literal=k, reason_fr="") for k in "水川海湖雨雪風雲雷霧"]
    gold = {"theme": "l'eau", "expect": "accept", "acceptable": "水川海湖雨雪風雲泉"}
    r = theme_gen.Result(theme="l'eau", refused=False, picks=picks, candidates=list(known))
    row = eval_themes.score(gold, r, known)
    assert row["precision"] == 0.8 and row["pass"] and row["off_list"] == "雷霧"

    refused = theme_gen.Result(theme="asdf", refused=True, refused_at="check")
    assert eval_themes.score({"theme": "asdf", "expect": "refuse"}, refused, known)["pass"]
