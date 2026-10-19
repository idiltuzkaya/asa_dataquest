"""
STEP 4 — Slide figures for the decomposition story (reads analysis/tables/, writes analysis/figures/).
    .venv/bin/python analysis/04_figures.py

Palette (validated with the dataviz skill's validate_palette.js, light surface, all-pairs):
    momentum #2a78d6 (blue) · fertility #eb6834 (orange) · migration #1baf7a (aqua)
    mortality = neutral grey + hatch: small, near-uniform effect -> de-emphasised, texture as secondary encoding.
Every coloured series is also direct-labelled (aqua is < 3:1 contrast, so labels are required).
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

ROOT = Path(__file__).resolve().parent.parent
TAB = ROOT / "analysis" / "tables"
FIG = ROOT / "analysis" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

C = {"momentum": "#2a78d6", "fertility": "#eb6834", "migration": "#1baf7a", "mortality": "#b9b7b0"}
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8d8b85", "#e6e5e1"
NAME = {"momentum": "Momentum (age structure)", "fertility": "Fertility", "migration": "Migration",
        "mortality": "Mortality decline"}
SHORT = {"United States of America": "USA", "Russian Federation": "Russia", "Republic of Korea": "S. Korea",
         "Democratic Republic of the Congo": "DR Congo", "Iran (Islamic Republic of)": "Iran", "United Kingdom": "UK",
         "United Arab Emirates": "UAE", "China, Hong Kong SAR": "Hong Kong", "Viet Nam": "Viet Nam"}
short = lambda s: SHORT.get(s, s)

plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"], "font.size": 10,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "axes.titlecolor": INK, "axes.titlesize": 12,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "xtick.color": INK2, "ytick.color": INK2,
    "xtick.major.size": 0, "ytick.major.size": 0, "legend.frameon": False, "savefig.dpi": 300,
    "figure.facecolor": "white", "axes.facecolor": "white", "hatch.color": "#8d8b85", "hatch.linewidth": 0.6,
})

D = pd.read_csv(TAB / "decomp_countries.csv")
A = pd.read_csv(TAB / "decomp_aggregates.csv")
WS = pd.read_csv(TAB / "world_scenarios_bn.csv", index_col=0)
NUM = json.loads((TAB / "decomp_numbers.json").read_text())
EFFECTS = ["momentum", "mortality", "fertility", "migration"]


def save(fig, name):
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("figure:", name)


def pct(f):  # growth factor -> "+50%" style label
    v = (f - 1) * 100
    return "0%" if abs(v) < 0.5 else f"{v:+.0f}%".replace("-", "−")


def dom_color(row):
    return C[row] if row in C else MUTED


# ============================================================ F1: TFR alone misleads
fig, ax = plt.subplots(figsize=(6.6, 4.6))
d = D.copy()
d["f"] = np.exp(d.total)
size = np.sqrt(d.pop_P0) / 2.2
ax.axvspan(0.6, 2.1, ymin=0, ymax=1, color="#f4f3f0", lw=0, zorder=0)
for dom in ["fertility", "momentum", "migration", "mortality"]:
    m = d.dominant == dom
    ax.scatter(d.TFR2024[m], d.f[m], s=size[m], color=C[dom], alpha=.8, edgecolor="white", lw=.6, zorder=3,
               hatch="////" if dom == "mortality" else None, label=f"{NAME[dom]} ({m.sum()})")
ax.set_yscale("log")
ax.axhline(1, color=INK2, lw=.8, zorder=2)
ax.axvline(2.1, color=INK2, lw=.8, zorder=2)
ax.set_xlim(0.6, 6.4)
ax.set_ylim(0.28, 5.2)
ticks = [0.33, 0.5, 0.75, 1, 1.5, 2, 3, 5]
ax.yaxis.set_major_locator(FixedLocator(ticks)); ax.yaxis.set_minor_locator(NullLocator())
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pct(v)))
ax.set_xlabel("Total fertility rate, 2024 (children per woman)")
ax.set_ylabel("Projected population change, 2024–2100")
ax.text(0.68, 4.75, "Below replacement", color=INK2, fontsize=8.5, va="top")
ax.text(2.14, 0.32, "replacement = 2.1", color=INK2, fontsize=8, va="bottom")
n_grow = NUM["below_repl_but_grows_2024_2100_n"]
ax.annotate(f"{n_grow} below-replacement countries\nstill grow to 2100", xy=(1.5, 1.12), xytext=(0.7, 2.6),
            fontsize=8.5, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=.7))
lab = {"India": (6, -12), "United States of America": (-30, 8), "Canada": (-38, 6), "China": (6, -4),
       "Republic of Korea": (6, -6), "Nigeria": (6, 2), "Niger": (-4, 8), "Japan": (6, -2), "Germany": (-8, -13),
       "Pakistan": (6, -6), "Marshall Islands": (6, -2), "Somalia": (-30, 8), "Türkiye": (-4, -13),
       "Australia": (-48, 0), "Ethiopia": (6, -4)}
for loc, (dx, dy) in lab.items():
    r = d[d.Location == loc].iloc[0]
    ax.annotate(short(loc), (r.TFR2024, r.f), xytext=(dx, dy), textcoords="offset points", fontsize=7.5, color=INK)
dot = lambda dom, lbl: plt.Line2D([], [], marker="o", lw=0, ms=7, color=C[dom], markeredgecolor="white", label=lbl)
leg = ax.legend(handles=[dot(k, f"{NAME[k]} ({(d.dominant == k).sum()})") for k in ["fertility", "momentum", "migration", "mortality"]],
                title="Largest driver of change", loc="lower right", fontsize=7.5, title_fontsize=8, handletextpad=.3, borderaxespad=.2)
leg._legend_box.align = "left"
ax.set_title("Same fertility, opposite futures")
save(fig, "F1_tfr_vs_growth.png")

# ============================================================ F2: world scenarios
fig, ax = plt.subplots(figsize=(6.4, 4.3))
hist = WS.loc[:2023, "Medium"]
proj = WS.loc[2024:2101]
ax.fill_between(proj.index, proj["Lower 95 PI"], proj["Upper 95 PI"], color="#ecebe7", lw=0, label="UN 95% interval")
ax.plot(hist.index, hist, color=INK, lw=2)
ax.plot(proj.index, proj["Medium"], color=INK, lw=2)
runs = [("Instant replacement zero migration", C["fertility"], "Replacement fertility (2.1) from 2024"),
        ("Momentum", C["momentum"], "Momentum only (age structure)"),
        ("Zero migration", C["migration"], "Zero migration")]
for col, cc, lbl in runs:
    ax.plot(proj.index, proj[col], color=cc, lw=2)
for txt, yv, bold in [(f"Replacement fertility  {proj['Instant replacement zero migration'].iloc[-1]:.1f}", 10.78, False),
                     (f"UN medium  {proj.Medium.iloc[-1]:.1f}", 10.32, True),
                     (f"Zero migration  {proj['Zero migration'].iloc[-1]:.1f}", 9.92, False),
                     (f"Momentum only  {proj['Momentum'].iloc[-1]:.1f}", 9.45, False)]:
    ax.text(2103, yv, txt, color=INK, fontsize=8, va="center", fontweight="bold" if bold else "normal")
ax.annotate(f"Constant fertility → {NUM['world_2101_bn_by_run']['Constant fertility']:.1f} bn (off chart)",
            xy=(2075, 12.3), xytext=(1952, 11.9), fontsize=8, color=INK2)
ax.axvline(2023.5, color=MUTED, lw=.7)
ax.text(2021, 2.55, "estimates", ha="right", fontsize=8, color=INK2)
ax.text(2026, 2.55, "projections", ha="left", fontsize=8, color=INK2)
ax.set_xlim(1950, 2101); ax.set_ylim(2.2, 12.5)
ax.set_ylabel("World population (billions)")
ax.set_title("Even 2.1 children per woman from today ends above the UN path")
# colour swatches as line legend (identity never colour-alone: end labels name each line)
handles = [plt.Line2D([], [], color=INK, lw=2, label="UN medium"),
           plt.Line2D([], [], color=C["fertility"], lw=2, label="Replacement fertility from 2024"),
           plt.Line2D([], [], color=C["momentum"], lw=2, label="Momentum only"),
           plt.Line2D([], [], color=C["migration"], lw=2, label="Zero migration"),
           Patch(color="#ecebe7", label="UN 95% interval")]
ax.legend(handles=handles, loc="upper left", fontsize=7.5, bbox_to_anchor=(0, .93))
save(fig, "F2_world_scenarios.png")


# ============================================================ F3: decomposition bars (regions & focus countries)
def decomp_bars(ax, frame, labels, title, xlim):
    y = np.arange(len(frame))[::-1]
    for yi, (_, r) in zip(y, frame.iterrows()):
        pos, neg = 0.0, 0.0
        for e in EFFECTS:
            v = r[e]
            left = pos if v >= 0 else neg + v
            ax.barh(yi, abs(v), left=left, height=.62, color=C[e], edgecolor="white", lw=1.2,
                    hatch="////" if e == "mortality" else None, zorder=3)
            if v >= 0: pos += v
            else: neg += v
        ax.scatter(r.total, yi, marker="D", s=34, color=INK, zorder=5, edgecolor="white", lw=.8)
        tx = max(pos, r.total) + 0.08
        ax.text(tx, yi, pct(np.exp(r.total)), va="center", fontsize=8, color=INK, fontweight="bold")
    ax.axvline(0, color=INK2, lw=.8, zorder=4)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=9)
    ax.grid(axis="y", visible=False)
    ticks = [np.log(v) for v in [0.25, 0.5, 1, 2, 4]]
    ax.set_xticks([t for t in ticks if xlim[0] <= t <= xlim[1]])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"×{np.exp(v):g}"))
    ax.set_xlim(*xlim)
    ax.set_title(title)


handles = [Patch(facecolor=C[e], edgecolor="white", hatch="////" if e == "mortality" else None, label=NAME[e]) for e in EFFECTS] + \
          [plt.Line2D([], [], marker="D", color=INK, lw=0, label="Net change")]

reg = A[A.level.isin(["World", "Region"])].set_index("name").loc[["World", "Africa", "Oceania", "Americas", "Asia", "Europe"]]
fig, ax = plt.subplots(figsize=(6.2, 3.6))
decomp_bars(ax, reg, reg.index.tolist(), "What drives each region's change, 2024–2100", (-0.85, 1.3))
ax.set_xlabel("Multiplicative effect on population (log scale; segments add up to the diamond)")
ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(.45, -.34), ncol=3, fontsize=7.5)
save(fig, "F3_region_decomposition.png")

focus = ["Nigeria", "Pakistan", "Ethiopia", "India", "Indonesia", "United States of America", "Canada", "Brazil",
         "Türkiye", "Germany", "Japan", "China", "Republic of Korea"]
fc = D.set_index("Location").loc[focus]
fig, ax = plt.subplots(figsize=(6.2, 4.6))
decomp_bars(ax, fc, [short(s) for s in focus], "Country engines: same outcome, different drivers", (-1.2, 1.45))
ax.set_xlabel("Multiplicative effect on population (log scale; colours as left)")
save(fig, "F4_country_decomposition.png")

# ============================================================ F5: engine map (momentum x fertility)
fig, ax = plt.subplots(figsize=(6.4, 4.8))
mx, fy = np.exp(D.momentum), np.exp(D.fertility)
for dom in ["fertility", "momentum", "migration", "mortality"]:
    m = D.dominant == dom
    ax.scatter(mx[m], fy[m], s=np.sqrt(D.pop_P0[m]) / 2.2, color=C[dom], alpha=.8, edgecolor="white", lw=.6, zorder=3,
               hatch="////" if dom == "mortality" else None, label=NAME[dom])
ax.set_xscale("log"); ax.set_yscale("log")
for k in [0.5, 1, 2, 4]:   # iso-lines: momentum x fertility = k (natural-increase factor before mortality)
    xs = np.geomspace(0.5, 2.0, 50)
    ax.plot(xs, k / xs, color=GRID if k != 1 else MUTED, lw=.8, zorder=1)
ax.axhline(1, color=INK2, lw=.6); ax.axvline(1, color=INK2, lw=.6)
ax.xaxis.set_major_locator(FixedLocator([0.6, 0.8, 1, 1.25, 1.5, 1.75])); ax.xaxis.set_minor_locator(NullLocator())
ax.yaxis.set_major_locator(FixedLocator([0.4, 0.6, 0.8, 1, 1.5, 2, 2.5])); ax.yaxis.set_minor_locator(NullLocator())
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"×{v:g}")); ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"×{v:g}"))
ax.set_xlim(0.55, 1.9); ax.set_ylim(0.33, 2.7)
ax.set_xlabel("Momentum effect (today's age structure)")
ax.set_ylabel("Fertility effect")
ax.text(1.02, 2.6, "Young & high fertility\n(most of sub-Saharan Africa)", ha="left", va="top", fontsize=8, color=INK2)
ax.text(1.88, 0.35, "Young, but fertility heading\nbelow replacement", ha="right", va="bottom", fontsize=8, color=INK2)
ax.text(0.56, 0.35, "Old & low fertility:\nmigration decides", ha="left", va="bottom", fontsize=8, color=INK2)
lab = {"India": (5, 3), "China": (5, -3), "Nigeria": (5, 2), "Niger": (5, 0), "Japan": (-30, 2), "Republic of Korea": (5, -2),
       "United States of America": (-8, 6), "Germany": (6, 3), "Italy": (-6, -13), "Brazil": (5, -2), "Pakistan": (-38, 6),
       "Türkiye": (5, -2), "Indonesia": (3, 5), "Democratic Republic of the Congo": (5, 0), "Bangladesh": (5, 2),
       "Ukraine": (5, -6), "Egypt": (4, 3)}
for loc, (dx, dy) in lab.items():
    r = D[D.Location == loc].iloc[0]
    ax.annotate(short(loc), (np.exp(r.momentum), np.exp(r.fertility)), xytext=(dx, dy), textcoords="offset points", fontsize=7.5, color=INK)
leg = ax.legend(handles=[dot(k, NAME[k]) for k in ["fertility", "momentum", "migration", "mortality"]],
                title="Largest driver", loc="upper left", fontsize=7.5, title_fontsize=8)
leg._legend_box.align = "left"
ax.set_title("Two forces separate the world's demographic futures")
save(fig, "F5_engine_map.png")

# ============================================================ F6: uncertainty vs size
fig, ax = plt.subplots(figsize=(6.2, 4.2))
u = D.dropna(subset=["pi95_ratio"])
ax.scatter(u.pop_P0 * 1e3, u.pi95_ratio, s=18, color="#52514e", alpha=.55, edgecolor="white", lw=.4, zorder=3)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("Population in 2024 (log scale)")
ax.set_ylabel("Width of UN 95% interval for 2100\n(upper ÷ lower bound)")
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: {1e3: "1k", 1e4: "10k", 1e5: "100k", 1e6: "1M", 1e7: "10M", 1e8: "100M", 1e9: "1B"}.get(v, "")))
ax.yaxis.set_major_locator(FixedLocator([2, 3, 5, 10, 30, 100, 300])); ax.yaxis.set_minor_locator(NullLocator())
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"×{v:g}"))
lab = {"Singapore": (5, 0), "Qatar": (5, 0), "India": (-10, 7), "China": (5, -6), "Nigeria": (5, 3), "Somalia": (5, 2),
       "Saint Kitts and Nevis": (5, 0), "Slovenia": (5, -6), "Spain": (5, 0), "Türkiye": (-46, 5), "Tuvalu": (5, 0)}
for loc, (dx, dy) in lab.items():
    r = u[u.Location == loc].iloc[0]
    ax.annotate(short(loc), (r.pop_P0 * 1e3, r.pi95_ratio), xytext=(dx, dy), textcoords="offset points", fontsize=7.5, color=INK)
rho = NUM["spearman_pi95_vs_logpop"]
ax.text(.03, .04, f"Spearman ρ = {rho:.2f}  (n = {len(u)})".replace("-", "−"), transform=ax.transAxes, ha="left", va="bottom", fontsize=8.5, color=INK)
ax.set_title("Small places carry the most uncertain futures")
save(fig, "F6_uncertainty_vs_size.png")
