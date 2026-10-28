"""Evaluate feature C on the 10-theme test set (src/eval/gold_themes.json), per pipeline config.

Configs: v1 (no step 0, k=30), check (step 0, k=30), check-k50 (step 0, k=50). Each theme RUNS times.
Pass rules, per run:
- expect "accept": not refused, 10 picks, all in KANJIDIC2 and in the candidates,
  and at least 8 of 10 in the hand-written acceptable set (precision >= 0.8);
- expect "refuse": refused.
Also reported: retriever hits = acceptable kanji among the candidates handed to Gemini.

Reads: src/eval/gold_themes.json, BigQuery, Vertex AI. Writes: out/data/eval_themes.csv.
Cost: 10 themes x 3 configs x 3 runs, ~2,000 tokens each: a few cents. Does not save themes.
"""

from __future__ import annotations

import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import bq_data  # noqa: E402
import theme_gen  # noqa: E402

GOLD = ROOT / "src" / "eval" / "gold_themes.json"
OUT = ROOT / "out" / "data" / "eval_themes.csv"
MIN_PRECISION = 0.8
RUNS = 3
CONFIGS = {"v1": dict(use_check=False, k=30), "check": dict(use_check=True, k=30),
           "check-k50": dict(use_check=True, k=50)}


def score(g: dict, r: theme_gen.Result, known: set[str]) -> dict:
    picks = [p.literal for p in r.picks]
    row = {"theme": g["theme"], "expect": g["expect"], "refused": r.refused, "refused_at": r.refused_at,
           "picks": "".join(picks), "precision": None, "retriever_hits": None, "off_list": "",
           "dropped": "".join(r.dropped), "reason": r.reason, "expanded": r.expanded, "tokens": r.tokens}
    if g["expect"] == "refuse":
        row["pass"] = r.refused
        return row
    acceptable = set(g["acceptable"]) & known
    row["precision"] = sum(k in acceptable for k in picks) / theme_gen.N_CARDS
    row["retriever_hits"] = len(set(r.candidates) & acceptable) if r.candidates else None
    row["off_list"] = "".join(k for k in picks if k not in acceptable)
    row["pass"] = (not r.refused and len(picks) == theme_gen.N_CARDS
                   and all(k in known for k in picks) and row["precision"] >= MIN_PRECISION)
    return row


def main() -> int:
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    ai, bq = theme_gen.vertex(), bq_data.client()
    known = set(bq_data.load_kanji(bq))
    jobs = [(c, run, g) for c in CONFIGS for run in range(RUNS) for g in gold]

    done = 0

    def work(job):
        nonlocal done
        c, run, g = job
        r = theme_gen.generate(g["theme"], ai, bq, **CONFIGS[c])
        done += 1
        print(f"  {done}/{len(jobs)} {c} {g['theme']}", flush=True)
        return {"config": c, "run": run, **score(g, r, known)}

    with ThreadPoolExecutor(4) as pool:
        rows = list(pool.map(work, jobs))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"{'theme':<28}" + "".join(f"{c:>18}" for c in CONFIGS))
    for g in gold:
        cells = []
        for c in CONFIGS:
            rs = [r for r in rows if r["config"] == c and r["theme"] == g["theme"]]
            cell = f"{sum(r['pass'] for r in rs)}/{RUNS}"
            hits = [r["retriever_hits"] for r in rs if r["retriever_hits"] is not None]
            if hits:
                cell += f" hits {min(hits)}-{max(hits)}"
            cells.append(f"{cell:>18}")
        print(f"{g['theme']:<28}" + "".join(cells))
    print(f"{'TOTAL':<28}" + "".join(
        f"{str(sum(r['pass'] for r in rows if r['config'] == c)) + '/' + str(RUNS * len(gold)):>18}" for c in CONFIGS))
    print(f"{'tokens':<28}" + "".join(f"{sum(r['tokens'] for r in rows if r['config'] == c):>18}" for c in CONFIGS))
    print(f"-> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
