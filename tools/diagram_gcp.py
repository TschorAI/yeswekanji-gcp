"""Draw the GCP architecture of yeswekanji-gcp: one icon card per service, numbered flows.

Reads: nothing (the architecture is written below, from src/ADR/).
Writes: out/figures/gcp_architecture.png and .pdf.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

from genau_kit import style
from genau_kit.style import C

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "figures"
W, H = 122, 60


# ---- icons, drawn around (x, y) with size s -------------------------------------------------

def icon_browser(ax, x, y, s, c):
    ax.add_patch(FancyBboxPatch((x - s, y - 0.75 * s), 2 * s, 1.5 * s,
                                boxstyle="round,pad=0,rounding_size=0.3", fc=C.surface, ec=c, lw=1.6, zorder=5))
    ax.add_patch(Rectangle((x - s, y + 0.4 * s), 2 * s, 0.35 * s, fc=c, ec=c, zorder=5))


def icon_laptop(ax, x, y, s, c):
    ax.add_patch(Rectangle((x - 0.8 * s, y - 0.3 * s), 1.6 * s, 1.0 * s, fc=C.surface, ec=c, lw=1.6, zorder=5))
    ax.add_patch(Polygon([(x - 1.1 * s, y - 0.55 * s), (x + 1.1 * s, y - 0.55 * s),
                          (x + 0.8 * s, y - 0.3 * s), (x - 0.8 * s, y - 0.3 * s)], fc=c, ec=c, zorder=5))


def icon_container(ax, x, y, s, c):
    for i, dy in enumerate((-0.55, 0.0, 0.55)):
        ax.add_patch(FancyBboxPatch((x - s, y + dy * s - 0.22 * s), 2 * s, 0.44 * s,
                                    boxstyle="round,pad=0,rounding_size=0.15",
                                    fc=c if i == 1 else C.surface, ec=c, lw=1.5, zorder=5))


def icon_db(ax, x, y, s, c):
    w, h = 1.7 * s, 1.5 * s
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=C.surface, ec="none", zorder=5))
    ax.plot([x - w / 2, x - w / 2], [y - h / 2, y + h / 2], color=c, lw=1.6, zorder=6)
    ax.plot([x + w / 2, x + w / 2], [y - h / 2, y + h / 2], color=c, lw=1.6, zorder=6)
    for yy in (y - h / 2, y):
        ax.add_patch(Arc((x, yy), w, 0.5 * s, theta1=180, theta2=360, ec=c, lw=1.6, zorder=6))
    ax.add_patch(Ellipse((x, y + h / 2), w, 0.5 * s, fc=c, ec=c, lw=1.6, zorder=6))


def icon_spark(ax, x, y, s, c):
    pts = []
    for i in range(8):
        r = s if i % 2 == 0 else 0.3 * s
        a = math.pi / 2 + i * math.pi / 4
        pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    ax.add_patch(Polygon(pts, fc=c, ec=c, zorder=5))


def icon_bucket(ax, x, y, s, c):
    ax.add_patch(Polygon([(x - s, y + 0.6 * s), (x + s, y + 0.6 * s), (x + 0.7 * s, y - 0.75 * s),
                          (x - 0.7 * s, y - 0.75 * s)], fc=C.surface, ec=c, lw=1.6, zorder=5))
    ax.add_patch(Ellipse((x, y + 0.6 * s), 2 * s, 0.45 * s, fc=c, ec=c, zorder=6))


def icon_speaker(ax, x, y, s, c):
    ax.add_patch(Polygon([(x - s, y - 0.3 * s), (x - 0.5 * s, y - 0.3 * s), (x, y - 0.75 * s),
                          (x, y + 0.75 * s), (x - 0.5 * s, y + 0.3 * s), (x - s, y + 0.3 * s)],
                         fc=c, ec=c, zorder=5))
    for r in (0.5, 0.9):
        ax.add_patch(Arc((x + 0.1 * s, y), 2 * r * s, 2 * r * s, theta1=-50, theta2=50, ec=c, lw=1.6, zorder=5))


def icon_log(ax, x, y, s, c):
    ax.add_patch(Rectangle((x - 0.7 * s, y - 0.8 * s), 1.4 * s, 1.6 * s, fc=C.surface, ec=c, lw=1.5, zorder=5))
    for dy in (0.4, 0.0, -0.4):
        ax.plot([x - 0.45 * s, x + 0.45 * s], [y + dy * s, y + dy * s], color=c, lw=1.4, zorder=6)


def icon_gear(ax, x, y, s, c):
    ax.plot(x, y, marker=(10, 1, 0), markersize=s * 11, color=c, zorder=5)
    ax.add_patch(Ellipse((x, y), 0.6 * s, 0.6 * s, fc=C.surface, ec="none", zorder=6))


def icon_boxes(ax, x, y, s, c):
    for dx, dy in ((-0.5, -0.45), (0.5, -0.45), (0.0, 0.45)):
        ax.add_patch(Rectangle((x + dx * s - 0.42 * s, y + dy * s - 0.38 * s), 0.84 * s, 0.76 * s,
                               fc=c, ec=C.surface, lw=1.2, zorder=5))


# ---- cards, arrows, badges --------------------------------------------------------------------

def card(ax, x, y, w, h, icon, name, tag, edge=C.accent, fill=C.surface):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2",
                                fc=fill, ec=edge, lw=1.4, zorder=2))
    s = min(h * 0.22, 2.2)
    icon(ax, x + 1.6 + s, y + h / 2, s, edge)
    tx = x + 3.4 + 2 * s
    ax.text(tx, y + h / 2 + 0.6, name, ha="left", va="bottom", fontsize=11.5, fontweight="bold", color=C.ink, zorder=7)
    ax.text(tx, y + h / 2 - 0.4, tag, ha="left", va="top", fontsize=9, color=C.muted, zorder=7)


def arrow(ax, a, b, color=C.accent, both=False):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="<|-|>" if both else "-|>", mutation_scale=13,
                                 lw=1.8, color=color, shrinkA=1, shrinkB=1, zorder=4))


def badge(ax, x, y, label, fill):
    ax.text(x, y, label, ha="center", va="center", fontsize=9.5, fontweight="bold", color=C.on_dark,
            zorder=8, bbox=dict(boxstyle="circle,pad=0.3", fc=fill, ec=C.bg, lw=1.5))


def along(ax, a, b, labels, lift=1.6):
    arrow(ax, a, b)
    for i, (label, fill) in enumerate(labels):
        f = (i + 1) / (len(labels) + 1)
        badge(ax, a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1]) + lift, label, fill)


def main() -> None:
    style.use()
    fig, ax = plt.subplots(figsize=(14, 6.9))
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.set_axis_off()

    ax.text(1, H - 0.5, "yeswekanji on Google Cloud", fontsize=17, fontweight="bold", color=C.ink, va="top")

    # GCP project frame
    ax.add_patch(FancyBboxPatch((20, 0.5), 74, 52, boxstyle="round,pad=0,rounding_size=1.5",
                                fc="none", ec=C.muted, lw=1.2, ls=(0, (4, 3)), zorder=1))
    ax.text(21.5, 51, "GCP project  ·  EU", fontsize=9.5, color=C.muted, va="top")

    T, F = C.dark, C.good  # badge colours: new theme, card flip
    card(ax, 1, 28, 18, 10, icon_browser, "Browser", "learner", edge=C.ink)
    card(ax, 25, 27, 24, 12, icon_container, "Cloud Run", "the Streamlit app", fill=C.accent_soft)
    card(ax, 25, 14, 16, 8, icon_log, "Logging", "stdout", edge=C.muted)
    card(ax, 62, 41, 29, 9, icon_spark, "Vertex AI", "Gemini + embeddings")
    card(ax, 62, 29, 29, 9, icon_db, "BigQuery", "kanji · vectors · reviews")
    card(ax, 62, 17, 29, 9, icon_bucket, "Cloud Storage", "MP3 files")
    card(ax, 62, 5, 29, 9, icon_speaker, "Text-to-Speech", "new MP3s")

    card(ax, 1, 2, 17, 9, icon_laptop, "Laptop", "your code", edge=C.warm_edge, fill=C.warm)
    card(ax, 22.5, 2, 18, 8, icon_gear, "Cloud Build", "builds", edge=C.warm_edge, fill=C.warm)
    card(ax, 43, 2, 17, 8, icon_boxes, "Registry", "the image", edge=C.warm_edge, fill=C.warm)

    # Request flows
    arrow(ax, (19, 33), (25, 33), color=C.ink, both=True)
    along(ax, (49, 36), (62, 45.5), [("1", T), ("3", T)])
    along(ax, (49, 33), (62, 33.5), [("2", T), ("4", T), ("a", F)])
    along(ax, (49, 30), (62, 21.5), [("b", F)])
    along(ax, (49, 28), (62, 9.5), [("c", F)], lift=-1.8)
    arrow(ax, (76.5, 14), (76.5, 17))
    arrow(ax, (32, 27), (32, 22), color=C.muted)

    # Build flow
    arrow(ax, (18, 6), (22.5, 6), color=C.warm_edge)
    arrow(ax, (40.5, 6), (43, 6), color=C.warm_edge)
    arrow(ax, (47.5, 10), (47.5, 27), color=C.warm_edge)

    # Legend
    x0 = 97
    groups = [("New theme", T, [("1", "check + expand"), ("2", "vector search"), ("3", "Gemini picks 10"),
                                ("4", "save")]),
              ("Card flip", F, [("a", "log the flip"), ("b", "play the MP3"), ("c", "make it if missing")])]
    y = 49
    for title, fill, items in groups:
        ax.text(x0, y, title, fontsize=11.5, fontweight="bold", color=C.ink, va="center")
        y -= 3.6
        for label, text in items:
            badge(ax, x0 + 1.2, y, label, fill)
            ax.text(x0 + 3.4, y, text, fontsize=10, color=C.ink, va="center")
            y -= 3.3
        y -= 2.4
    for color, text in ((C.accent, "request"), (C.warm_edge, "build"), (C.muted, "logs")):
        ax.plot([x0, x0 + 4], [y, y], color=color, lw=1.8)
        ax.text(x0 + 5.2, y, text, fontsize=9.5, color=C.muted, va="center")
        y -= 2.8

    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"gcp_architecture.{ext}", dpi=200, bbox_inches="tight", facecolor=C.bg)
    print(f"wrote {OUT.relative_to(ROOT)}/gcp_architecture.png and .pdf")


if __name__ == "__main__":
    main()
