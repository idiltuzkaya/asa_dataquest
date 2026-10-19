"""
STEP 2 — Detailed EDA on the cleaned WPP2024 country panel.

Run from the project root (after 01_clean_data.py):
    uv run --with pandas --with numpy --with matplotlib --with seaborn --with scipy --with scikit-learn python eda/02_eda_analysis.py

Writes figures to eda/figures/, tables to eda/tables/, and eda/tables/key_numbers.json.
All "population-weighted" aggregates use TPopulation1July as weights.
Statistical tests here are DESCRIPTIVE: UN series (esp. projections) are modelled outputs, not random samples,
and country-years are serially dependent, so p-values are reported as effect-size screening, not formal inference.
"""
import json
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import PowerTransformer, StandardScaler

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

ROOT = Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "clean" / "wpp2024_countries_clean.csv"
RAW = ROOT / "data" / "WPP2024_Demographic_Indicators_Medium_csv.gz"
FIG = ROOT / "eda" / "figures"
TAB = ROOT / "eda" / "tables"
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

REGION_ORDER = ["Africa", "Asia", "Europe", "Americas", "Oceania"]
PAL = {"Africa": "#D1495B", "Asia": "#EDAE49", "Europe": "#00798C", "Americas": "#30638E", "Oceania": "#7A9E7E"}
LAST_EST = 2023
KEY = ["MedianAgePop", "TFR", "LEx", "LE65", "IMR", "Q1550", "CBR", "CDR", "PopGrowthRate", "CNMR", "MAC", "PopSexRatio"]
LABEL = {"MedianAgePop": "Median age (yrs)", "TFR": "Total fertility rate", "LEx": "Life expectancy at birth (yrs)",
         "LE65": "Life expectancy at 65 (yrs)", "IMR": "Infant mortality (per 1,000)", "Q1550": "Adult mortality 15-50 (per 1,000)",
         "CBR": "Crude birth rate", "CDR": "Crude death rate", "PopGrowthRate": "Population growth (%)",
         "CNMR": "Net migration rate (per 1,000)", "MAC": "Mean age at childbearing", "PopSexRatio": "Sex ratio (M per 100 F)",
         "TPopulation1Jan": "Population (thousands)", "PopDensity": "Density (per km2)"}

sns.set_theme(style="whitegrid", context="notebook", font="DejaVu Sans")
plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 150, "axes.titleweight": "bold", "axes.titlesize": 12,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False})
NUM = {}  # key numbers for the report


def save(fig, name):
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  figure:", name)


def shade_proj(ax):
    ax.axvspan(LAST_EST + 0.5, 2100, color="grey", alpha=0.08, lw=0)
    ax.axvline(LAST_EST + 0.5, color="grey", ls="--", lw=0.8)


def wmean(df, col, by, w="TPopulation1July"):
    t = df.assign(_x=df[col] * df[w])
    g = t.groupby(by)
    return (g["_x"].sum() / g[w].sum()).rename(col)


df = pd.read_csv(CLEAN)
raw = pd.read_csv(RAW, compression="gzip", encoding="utf-8-sig", low_memory=False)
c23 = df[df.Time == 2023].copy()
core = df[df.CoreCountry]
print(f"clean panel {df.shape}; 2023 cross-section {c23.shape}")

# ============================================================ 1. structure & data quality
print("\n[1] structure & quality")
tc = raw.groupby(raw.LocTypeName.fillna("Unlabelled grouping")).agg(locations=("LocID", "nunique"), rows=("LocID", "size")) \
        .sort_values("locations")
fig, ax = plt.subplots(figsize=(9, 4.2))
cols = ["#00798C" if i == "Country/Area" else "#B8B8B8" for i in tc.index]
ax.barh(tc.index, tc["locations"], color=cols)
for y, (v, r) in enumerate(zip(tc["locations"], tc["rows"])):
    ax.text(v + 3, y, f"{v} locations / {r:,} rows", va="center", fontsize=9)
ax.set_xlabel("Distinct locations in raw Medium file"); ax.set_xlim(0, 330)
ax.set_title("Raw file mixes 237 countries with 318 aggregate groupings (naive sum = 44.8x World)")
save(fig, "f01_location_types.png")
tc.to_csv(TAB / "t01_location_types.csv")

rawc = raw[raw.LocTypeName == "Country/Area"]
numcols = rawc.select_dtypes("number").columns.difference(["SortOrder", "LocID", "LocTypeID", "ParentID", "VarID", "SDMX_code", "Time"])
miss_raw = rawc[numcols].isna().mean().sort_values(ascending=False)
miss_raw = miss_raw[miss_raw > 0]
dtn = df.assign(dt_na=df.DoublingTime.isna())
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
ax = axes[0]
x = rawc.groupby("Time")[list(numcols)].apply(lambda g: g.isna().mean().mean())
ax.plot(x.index, x.values * 100, color="#D1495B"); ax.set_ylabel("% of numeric cells missing"); ax.set_xlabel("Year")
ax.annotate("2101: only TPopulation1Jan populated\n(dropped in cleaning)", xy=(2101, x.loc[2101] * 100), xytext=(1990, 70),
            arrowprops=dict(arrowstyle="->", color="grey"), fontsize=9)
ax.set_title("Missingness by year in raw country rows")
ax = axes[1]
s = dtn.groupby("Time").dt_na.mean() * 100
ax.plot(s.index, s.values, color="#30638E"); shade_proj(ax)
ax.set_title("After cleaning: only DoublingTime is missing\n(structural: undefined when growth <= 0)")
ax.set_ylabel("% of countries with DoublingTime NaN"); ax.set_xlabel("Year")
save(fig, "f02_missingness.png")
NUM["doubling_na_share"] = float(df.DoublingTime.isna().mean())
NUM["doubling_na_when_growth_le0"] = float((df.loc[df.DoublingTime.isna(), "PopGrowthRate"] <= 0).mean())

# accounting identities worth knowing (feeds multicollinearity discussion)
ident = {
    "NatChangeRT_minus_(CBR-CDR)_maxabs": float((df.NatChangeRT - (df.CBR - df.CDR)).abs().max()),
    "PopGrowthRate*10_minus_(NatChangeRT+CNMR)_maxabs": float((df.PopGrowthRate * 10 - (df.NatChangeRT + df.CNMR)).abs().quantile(0.99)),
    "corr_IMR_Q5": float(df.IMR.corr(df.Q5)),
    "corr_TFR_CBR": float(df.TFR.corr(df.CBR)),
}
NUM["identities"] = ident
print("  identities:", ident)

# ============================================================ 2. univariate distributions
print("\n[2] univariate")
desc_rows = []
for col in ["TPopulation1Jan", "PopDensity"] + KEY:
    for name, s in [("2023 cross-section", c23[col]), ("pooled 1950-2100", df[col])]:
        s = s.dropna()
        lg = np.log10(s[s > 0]) if (s > 0).all() else None
        desc_rows.append({"indicator": col, "sample": name, "n": len(s), "mean": s.mean(), "sd": s.std(), "min": s.min(),
                          "p25": s.quantile(.25), "median": s.median(), "p75": s.quantile(.75), "max": s.max(),
                          "skew": stats.skew(s), "excess_kurtosis": stats.kurtosis(s),
                          "skew_after_log10": stats.skew(lg) if lg is not None else np.nan,
                          "cv": s.std() / s.mean() if s.mean() else np.nan})
desc = pd.DataFrame(desc_rows)
desc.to_csv(TAB / "t02_descriptive_stats.csv", index=False)
NUM["skew_2023"] = {r.indicator: round(r.skew, 2) for r in desc[desc["sample"] == "2023 cross-section"].itertuples()}
NUM["skew_log_2023"] = {r.indicator: (None if np.isnan(r.skew_after_log10) else round(r.skew_after_log10, 2))
                        for r in desc[desc["sample"] == "2023 cross-section"].itertuples()}

plot_cols = [("TPopulation1Jan", True), ("PopDensity", True), ("MedianAgePop", False), ("TFR", False), ("LEx", False), ("IMR", True),
             ("CBR", False), ("CDR", False), ("PopGrowthRate", False), ("CNMR", False), ("PopSexRatio", True), ("MAC", False)]
fig, axes = plt.subplots(3, 4, figsize=(16, 9))
for ax, (col, lg) in zip(axes.ravel(), plot_cols):
    s = c23[col].dropna()
    if lg:
        sns.histplot(s, log_scale=True, bins=30, kde=True, ax=ax, color="#30638E")
    else:
        sns.histplot(s, bins=30, kde=True, ax=ax, color="#30638E")
    ax.axvline(s.median(), color="#D1495B", ls="--", lw=1)
    ax.set_title(f"{LABEL[col]}", fontsize=10); ax.set_xlabel(f"skew={stats.skew(s):.2f}" + (" (log axis)" if lg else "")); ax.set_ylabel("")
fig.suptitle("Cross-country distributions, 2023 (237 countries/areas; dashed = median)", fontweight="bold", y=1.0)
fig.tight_layout()
save(fig, "f03_distributions_2023.png")

yrs_show = [1950, 1985, 2023, 2060, 2100]
fig, axes = plt.subplots(1, 4, figsize=(17, 3.8))
for ax, col, lg in zip(axes, ["LEx", "TFR", "MedianAgePop", "IMR"], [False, False, False, True]):
    for y, cc in zip(yrs_show, sns.color_palette("viridis", len(yrs_show))):
        s = df.loc[df.Time == y, col]
        sns.kdeplot(s, ax=ax, color=cc, label=str(y), fill=True, alpha=.12, log_scale=lg, warn_singular=False)
    ax.set_title(LABEL[col], fontsize=10); ax.set_xlabel(""); ax.set_ylabel("")
axes[0].legend(title="Year", fontsize=8)
fig.suptitle("The whole cross-country distribution shifts (and changes shape) over time", fontweight="bold", y=1.04)
save(fig, "f04_distribution_shift.png")
# bimodality in 1950 LEx and TFR (Hartigan-style quick check via KDE peaks)
from scipy.signal import find_peaks
def n_modes(s):
    g = np.linspace(s.min(), s.max(), 400); k = stats.gaussian_kde(s.dropna())(g)
    return len(find_peaks(k, prominence=k.max() * 0.05)[0])
NUM["modes"] = {f"{col}_{y}": n_modes(df.loc[df.Time == y, col]) for col in ["LEx", "TFR", "MedianAgePop"] for y in [1950, 1985, 2023, 2060, 2100]}

fig, axes = plt.subplots(2, 3, figsize=(15, 8))
for ax, col in zip(axes.ravel(), ["LEx", "TFR", "MedianAgePop", "IMR", "CNMR", "PopGrowthRate"]):
    sns.boxplot(data=c23, x="Region", y=col, order=REGION_ORDER, palette=PAL, ax=ax, fliersize=3, linewidth=1)
    sns.stripplot(data=c23, x="Region", y=col, order=REGION_ORDER, color="k", size=2, alpha=.35, ax=ax)
    ax.set_title(LABEL[col], fontsize=10); ax.set_xlabel(""); ax.set_ylabel("")
fig.suptitle("Regional distributions, 2023", fontweight="bold")
fig.tight_layout()
save(fig, "f05_boxplots_by_region_2023.png")

kw_rows = []
for col in ["LEx", "TFR", "MedianAgePop", "IMR", "CNMR", "PopGrowthRate", "TPopulation1Jan"]:
    groups = [g[col].dropna().values for _, g in c23.groupby("Region")]
    H, p = stats.kruskal(*groups)
    n = sum(len(g) for g in groups); k = len(groups)
    kw_rows.append({"indicator": col, "kruskal_H": H, "p_value": p, "epsilon_squared": (H - k + 1) / (n - k)})
kw = pd.DataFrame(kw_rows); kw.to_csv(TAB / "t03_kruskal_by_region_2023.csv", index=False)
NUM["kruskal_eps2"] = {r.indicator: round(r.epsilon_squared, 3) for r in kw.itertuples()}

# ============================================================ 3. temporal structure
print("\n[3] temporal")
world = df.groupby("Time").agg(pop=("TPopulation1Jan", "sum")).reset_index()
rp = df.groupby(["Time", "Region"]).TPopulation1Jan.sum().unstack()[REGION_ORDER]
fig, axes = plt.subplots(1, 2, figsize=(14, 4.6))
ax = axes[0]
ax.plot(world.Time, world["pop"] / 1e6, color="k", lw=2); shade_proj(ax)
ax.set_ylabel("World population (billions)"); ax.set_xlabel("Year")
pk = world.loc[world["pop"].idxmax()]
ax.scatter([pk.Time], [pk["pop"] / 1e6], color="#D1495B", zorder=5)
ax.annotate(f"peak {pk['pop']/1e6:.2f}bn in {int(pk.Time)}", (pk.Time, pk["pop"] / 1e6), xytext=(1985, 9.2), arrowprops=dict(arrowstyle="->"), fontsize=9)
ax.set_title("World population: estimates (white) vs medium projection (grey)")
ax = axes[1]
(rp.div(rp.sum(1), axis=0) * 100).plot.area(ax=ax, color=[PAL[r] for r in REGION_ORDER], lw=0, alpha=.9); shade_proj(ax)
ax.set_ylabel("% of world population"); ax.set_xlabel("Year"); ax.set_title("Regional share of world population"); ax.legend(loc="center left", bbox_to_anchor=(1, .5))
ax.set_ylim(0, 100)
fig.tight_layout(); save(fig, "f06_world_population.png")
NUM["world_pop_peak_year"] = int(pk.Time); NUM["world_pop_peak_bn"] = float(pk["pop"] / 1e6)
NUM["world_pop_1950_2023_2100_bn"] = [float(world.loc[world.Time == y, "pop"].iloc[0] / 1e6) for y in (1950, 2023, 2100)]
share = rp.div(rp.sum(1), axis=0) * 100
NUM["region_share_1950_2023_2100"] = {r: [round(float(share.loc[y, r]), 1) for y in (1950, 2023, 2100)] for r in REGION_ORDER}

fig, axes = plt.subplots(2, 2, figsize=(14, 8.5))
reg_series = {}
for ax, col in zip(axes.ravel(), ["LEx", "TFR", "MedianAgePop", "PopGrowthRate"]):
    for r in REGION_ORDER:
        s = wmean(df[df.Region == r], col, "Time"); reg_series[(col, r)] = s
        ax.plot(s.index, s.values, color=PAL[r], lw=2, label=r)
    sw = wmean(df, col, "Time"); ax.plot(sw.index, sw.values, color="k", lw=1.5, ls=":", label="World"); reg_series[(col, "World")] = sw
    shade_proj(ax); ax.set_title(LABEL[col] + " (population-weighted)"); ax.set_xlabel("")
axes[0, 0].legend(ncol=2, fontsize=8)
axes[1, 1].axhline(0, color="k", lw=.6)
fig.tight_layout(); save(fig, "f07_regional_trajectories.png")
NUM["world_weighted"] = {col: [round(float(reg_series[(col, 'World')].loc[y]), 2) for y in (1950, 2023, 2100)] for col in ["LEx", "TFR", "MedianAgePop", "PopGrowthRate"]}
NUM["region_weighted_2023"] = {r: {col: round(float(reg_series[(col, r)].loc[2023]), 2) for col in ["LEx", "TFR", "MedianAgePop"]} for r in REGION_ORDER}
NUM["region_weighted_2100"] = {r: {col: round(float(reg_series[(col, r)].loc[2100]), 2) for col in ["LEx", "TFR", "MedianAgePop"]} for r in REGION_ORDER}

sub = df.groupby(["SubRegion", "Time"]).apply(lambda g: pd.Series({c: np.average(g[c], weights=g.TPopulation1July) for c in ["LEx", "TFR", "MedianAgePop"]})).reset_index()
order = df.drop_duplicates("SubRegion").assign(r=lambda d: d.Region.map({k: i for i, k in enumerate(REGION_ORDER)})).sort_values(["r", "SubRegion"]).SubRegion.tolist()
fig, axes = plt.subplots(1, 3, figsize=(18, 7), sharey=True)
for ax, col, cm in zip(axes, ["LEx", "TFR", "MedianAgePop"], ["viridis", "magma_r", "cividis"]):
    pv = sub.pivot(index="SubRegion", columns="Time", values=col).loc[order, list(range(1950, 2101, 5))]
    sns.heatmap(pv, ax=ax, cmap=cm, cbar_kws={"shrink": .7}, linewidths=0)
    ax.axvline(list(range(1950, 2101, 5)).index(2025) + .5, color="white", lw=1.5, ls="--")
    ax.set_title(LABEL[col]); ax.set_xlabel(""); ax.set_ylabel("")
fig.suptitle("Sub-regional trajectories (population-weighted, 5-year steps; dashed = start of projection)", fontweight="bold")
fig.tight_layout(); save(fig, "f08_subregion_heatmaps.png")
sub.to_csv(TAB / "t04_subregion_weighted_means.csv", index=False)

disp = df.groupby("Time").agg(**{f"{c}_{a}": (c, f) for c in ["LEx", "TFR", "MedianAgePop"] for a, f in
                                 [("sd", "std"), ("p10", lambda s: s.quantile(.1)), ("p90", lambda s: s.quantile(.9)), ("med", "median")]})
fig, axes = plt.subplots(1, 3, figsize=(16, 4.2))
for ax, col in zip(axes, ["LEx", "TFR", "MedianAgePop"]):
    ax.fill_between(disp.index, disp[f"{col}_p10"], disp[f"{col}_p90"], color="#30638E", alpha=.25, label="P10-P90 across countries")
    ax.plot(disp.index, disp[f"{col}_med"], color="#30638E", lw=2, label="median")
    ax2 = ax.twinx(); ax2.plot(disp.index, disp[f"{col}_sd"], color="#D1495B", lw=1.5, ls="--"); ax2.set_ylabel("cross-country SD", color="#D1495B"); ax2.grid(False)
    shade_proj(ax); ax.set_title(LABEL[col]); ax.set_xlabel("")
axes[0].legend(fontsize=8, loc="upper left")
fig.suptitle("Convergence or divergence? Spread across countries over time", fontweight="bold", y=1.03)
fig.tight_layout(); save(fig, "f09_cross_country_dispersion.png")
NUM["dispersion_sd"] = {c: {y: round(float(disp.loc[y, f"{c}_sd"]), 2) for y in (1950, 1990, 2023, 2060, 2100)} for c in ["LEx", "TFR", "MedianAgePop"]}
NUM["dispersion_peak_year"] = {c: int(disp[f"{c}_sd"].idxmax()) for c in ["LEx", "TFR", "MedianAgePop"]}

# concentration / rank mobility
piv = df.pivot(index="Time", columns="Location", values="TPopulation1Jan")
ys = [1950, 1975, 2000, 2023, 2050, 2075, 2100]
top = set()
for y in ys:
    top |= set(piv.loc[y].nlargest(10).index)
ranks = piv.loc[ys].rank(axis=1, ascending=False).T.loc[sorted(top)]
fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
ax = axes[0]
for loc, row in ranks.iterrows():
    ax.plot(ys, row.values, marker="o", lw=1.6, color=PAL[df.loc[df.Location == loc, "Region"].iloc[0]], alpha=.9)
    if row.values[-1] > 30:
        continue_label = False
    else:
        continue_label = True
    if continue_label: ax.text(ys[-1] + 3, row.values[-1], loc.replace("United States of America", "USA").replace("Russian Federation", "Russia")
            .replace("Democratic Republic of the Congo", "DR Congo").replace("United Republic of Tanzania", "Tanzania")
            .replace("Iran (Islamic Republic of)", "Iran"), va="center", fontsize=7.5)
ax.set_ylim(30, 0.5); ax.set_xlim(1945, 2125); ax.set_ylabel("Population rank (clipped at 30)"); ax.set_title("Rank mobility of the largest countries")
ax = axes[1]
t10 = piv.apply(lambda r: r.nlargest(10).sum() / r.sum() * 100, axis=1)
ax.plot(t10.index, t10.values, color="k", lw=2); shade_proj(ax); ax.set_ylabel("% of world population in top-10 countries")
ax.set_title("Population concentration"); ax.set_xlabel("Year")
fig.tight_layout(); save(fig, "f10_rank_mobility_concentration.png")
NUM["top10_share"] = {int(y): round(float(t10.loc[y]), 1) for y in (1950, 2023, 2100)}
NUM["top5_2023"] = piv.loc[2023].nlargest(5).round(0).to_dict()
NUM["top5_2100"] = piv.loc[2100].nlargest(5).round(0).to_dict()

# ============================================================ 4. bivariate / correlation
print("\n[4] correlation")
pooled_sp = df[KEY].corr(method="spearman")
cs_sp = c23[KEY].corr(method="spearman")
within = df[KEY] - df.groupby("LocID")[KEY].transform("mean")
within_corr = within.corr()
between = df.groupby("LocID")[KEY].mean().corr(method="spearman")
fig, axes = plt.subplots(1, 3, figsize=(22, 6.6))
for ax, m, t in zip(axes, [pooled_sp, between, within_corr], ["Pooled Spearman (all country-years)", "BETWEEN countries (country means, Spearman)", "WITHIN countries (demeaned by country, Pearson)"]):
    sns.heatmap(m, ax=ax, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1, annot_kws={"size": 7}, cbar=False, square=True)
    ax.set_title(t, fontsize=11)
fig.tight_layout(); save(fig, "f11_correlation_pooled_between_within.png")
pooled_sp.to_csv(TAB / "t05_corr_pooled_spearman.csv"); within_corr.to_csv(TAB / "t05_corr_within.csv"); between.to_csv(TAB / "t05_corr_between.csv")
# sign-flip pairs (Simpson-type)
flips = []
for i, a in enumerate(KEY):
    for b in KEY[i + 1:]:
        if np.sign(between.loc[a, b]) != np.sign(within_corr.loc[a, b]) and min(abs(between.loc[a, b]), abs(within_corr.loc[a, b])) > .1:
            flips.append({"a": a, "b": b, "between": round(between.loc[a, b], 2), "within": round(within_corr.loc[a, b], 2)})
NUM["sign_flips_between_vs_within"] = flips
NUM["corr_pooled_pairs"] = {f"{a}~{b}": round(float(pooled_sp.loc[a, b]), 2) for a, b in [("TFR", "MedianAgePop"), ("LEx", "MedianAgePop"), ("LEx", "TFR"), ("IMR", "LEx"), ("CBR", "TFR"), ("PopGrowthRate", "CNMR"), ("PopGrowthRate", "TFR"), ("CDR", "LEx"), ("MAC", "TFR")]}
NUM["corr_within_pairs"] = {f"{a}~{b}": round(float(within_corr.loc[a, b]), 2) for a, b in [("TFR", "MedianAgePop"), ("LEx", "MedianAgePop"), ("LEx", "TFR"), ("CDR", "LEx"), ("PopGrowthRate", "CNMR"), ("MAC", "TFR")]}

# VIF on pooled standardised key indicators (log-transformed skewed vars)
Xv = df[KEY].copy()
for col in ["IMR", "Q1550"]:
    Xv[col] = np.log(Xv[col])
Xs = StandardScaler().fit_transform(Xv.dropna())
vif = pd.Series(np.diag(np.linalg.inv(np.corrcoef(Xs.T))), index=KEY).sort_values(ascending=False).rename("VIF")
vif.to_frame().to_csv(TAB / "t06_vif.csv")
NUM["vif"] = vif.round(1).to_dict()

# full clustered correlation structure (all 60+ numeric indicators, 2023, Spearman) -> redundancy blocks
allnum = [c for c in df.select_dtypes("number").columns if c not in ["LocID", "Time"] and df[c].nunique() > 2]
cg = sns.clustermap(c23[allnum].corr(method="spearman").fillna(0), cmap="RdBu_r", vmin=-1, vmax=1, figsize=(17, 17),
                    xticklabels=True, yticklabels=True, cbar_pos=(0.02, 0.85, 0.02, 0.1))
cg.ax_heatmap.tick_params(labelsize=6)
cg.figure.suptitle("All numeric indicators, 2023 (Spearman, hierarchically clustered): redundancy blocks", y=1.0, fontweight="bold")
cg.savefig(FIG / "f12_clustered_correlation_all.png", dpi=130); plt.close(cg.figure); print("  figure: f12_clustered_correlation_all.png")

fig, axes = plt.subplots(2, 2, figsize=(14, 10.5))
bub = c23.assign(size=np.sqrt(c23.TPopulation1Jan))
specs = [("TFR", "LEx", False, "TFR vs life expectancy"), ("IMR", "LEx", True, "Infant mortality (log) vs life expectancy"),
         ("TFR", "MedianAgePop", False, "TFR vs median age"), ("PopGrowthRate", "CNMR", False, "Growth vs net-migration rate")]
for ax, (xc, yc, lgx, t) in zip(axes.ravel(), specs):
    for r in REGION_ORDER:
        d = bub[bub.Region == r]; ax.scatter(d[xc], d[yc], s=d["size"] / 3.5, color=PAL[r], alpha=.65, edgecolor="white", lw=.4, label=r)
    if lgx: ax.set_xscale("log")
    xx = np.log(c23[xc]) if lgx else c23[xc]
    rho = stats.spearmanr(c23[xc], c23[yc])[0]
    ax.set_xlabel(LABEL[xc]); ax.set_ylabel(LABEL[yc]); ax.set_title(f"{t}  (Spearman {rho:.2f}, 2023)")
axes[0, 0].legend(fontsize=8, markerscale=.5)
fig.suptitle("Bivariate structure, 2023 (bubble area ~ sqrt(population))", fontweight="bold")
fig.tight_layout(); save(fig, "f13_bivariate_scatter_2023.png")

# development paths (fertility x mortality plane)
paths = ["India", "China", "Nigeria", "Niger", "Republic of Korea", "Brazil", "Germany", "Egypt", "Bangladesh"]
short = {"Republic of Korea": "S. Korea", "United States of America": "USA", "Iran (Islamic Republic of)": "Iran"}
fig, ax = plt.subplots(figsize=(10.5, 7))
for loc in paths:
    d = df[(df.Location == loc) & (df.Time % 5 == 0)].sort_values("Time"); col = PAL[d.Region.iloc[0]]
    ax.plot(d.TFR, d.LEx, color=col, lw=1.6, alpha=.9, marker=".", ms=4)
    ax.scatter(d.TFR.iloc[0], d.LEx.iloc[0], color=col, s=45, marker="o", zorder=5); ax.scatter(d.TFR.iloc[-1], d.LEx.iloc[-1], color=col, s=55, marker="s", zorder=5)
    ax.annotate(short.get(loc, loc), (d.TFR.iloc[0], d.LEx.iloc[0]), xytext=(5, -10), textcoords="offset points", fontsize=8, color=col, fontweight="bold")
ax.set_xlabel("Total fertility rate"); ax.set_ylabel("Life expectancy at birth"); ax.invert_xaxis()
ax.set_title("Demographic-transition paths, 5-year steps: 1950 (circle) -> 2100 (square); x-axis reversed")
save(fig, "f14_transition_paths.png")

# ============================================================ 5. multivariate structure (PCA / clusters)
print("\n[5] PCA & clustering")
feat = ["MedianAgePop", "TFR", "LEx", "LE65", "IMR", "Q1550", "CBR", "CDR", "PopGrowthRate", "CNMR", "MAC", "PopSexRatio"]
Xp = c23.set_index("Location")[feat].dropna()
Z = PowerTransformer(method="yeo-johnson", standardize=True).fit_transform(Xp)
pca = PCA().fit(Z); scores = pca.transform(Z)
ev = pca.explained_variance_ratio_
loadings = pd.DataFrame(pca.components_[:3].T, index=feat, columns=["PC1", "PC2", "PC3"])
loadings.to_csv(TAB / "t07_pca_loadings_2023.csv")
NUM["pca_var"] = [round(float(v) * 100, 1) for v in ev[:4]]
NUM["pca_loadings_top"] = {pc: loadings[pc].abs().sort_values(ascending=False).head(4).index.tolist() for pc in ["PC1", "PC2"]}
k_range = range(2, 9)
k_max = int(np.searchsorted(np.cumsum(ev), .90) + 1)
sil = {k: silhouette_score(scores[:, :k_max], KMeans(k, n_init=20, random_state=0).fit_predict(scores[:, :k_max])) for k in k_range}
kbest = max(sil, key=sil.get)
lab = KMeans(kbest, n_init=20, random_state=0).fit_predict(scores[:, :k_max])
NUM["silhouette"] = {k: round(v, 3) for k, v in sil.items()}; NUM["k_best"] = kbest; NUM["pcs_for_90pct"] = k_max
reg23 = c23.set_index("Location").loc[Xp.index, "Region"]
fig, axes = plt.subplots(1, 3, figsize=(18, 5.4))
axes[0].bar(range(1, len(ev) + 1), ev * 100, color="#30638E"); axes[0].plot(range(1, len(ev) + 1), np.cumsum(ev) * 100, color="#D1495B", marker="o")
axes[0].set_xlabel("Principal component"); axes[0].set_ylabel("% variance (bars) / cumulative (line)"); axes[0].set_title("PCA scree, 12 indicators, 2023")
ax = axes[1]
for r in REGION_ORDER:
    m = (reg23 == r).values; ax.scatter(scores[m, 0], scores[m, 1], color=PAL[r], s=22, alpha=.8, label=r)
for f_, (a, b) in zip(feat, pca.components_[:2].T):
    ax.arrow(0, 0, a * 5, b * 5, color="k", alpha=.5, head_width=.08); ax.text(a * 5.4, b * 5.4, f_, fontsize=7)
ax.set_xlabel(f"PC1 ({ev[0]*100:.0f}%)"); ax.set_ylabel(f"PC2 ({ev[1]*100:.0f}%)"); ax.set_title("Biplot coloured by region"); ax.legend(fontsize=7)
ax = axes[2]
ax.plot(list(sil.keys()), list(sil.values()), marker="o", color="#30638E"); ax.set_xlabel("k"); ax.set_ylabel("Silhouette"); ax.set_title(f"k-means on {k_max} PCs: best k={kbest}")
fig.tight_layout(); save(fig, "f15_pca_clusters.png")
cl = pd.DataFrame({"Location": Xp.index, "cluster": lab, "Region": reg23.values})
cl.to_csv(TAB / "t08_clusters_2023.csv", index=False)
NUM["cluster_region_crosstab"] = pd.crosstab(cl.cluster, cl.Region).to_dict()

# ============================================================ 6. migration
print("\n[6] migration")
mig = df[(df.Time >= 2000) & (df.Time <= 2023)].groupby("Location").NetMigrations.sum().sort_values()
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
sel = pd.concat([mig.head(10), mig.tail(10)])
axes[0].barh(sel.index, sel.values / 1e3, color=["#D1495B" if v < 0 else "#00798C" for v in sel.values]); axes[0].set_xlabel("Cumulative net migrants 2000-2023 (millions)")
axes[0].set_title("Largest net senders / receivers"); axes[0].tick_params(axis="y", labelsize=8)
ax = axes[1]
nc = c23
for r in REGION_ORDER:
    d = nc[nc.Region == r]; ax.scatter(d.NatChangeRT, d.CNMR, color=PAL[r], s=24, alpha=.75, label=r)
ax.axhline(0, color="k", lw=.5); ax.axvline(0, color="k", lw=.5)
ax.set_xlabel("Natural change (per 1,000)"); ax.set_ylabel("Net migration (per 1,000)"); ax.set_title("Growth = natural change + migration, 2023"); ax.legend(fontsize=7)
ax = axes[2]
hp = df.assign(mig_dominant=(df.CNMR.abs() > df.NatChangeRT.abs()))
sh = hp.groupby(["Time", "Region"]).mig_dominant.mean().unstack()[REGION_ORDER] * 100
for r in REGION_ORDER:
    ax.plot(sh.index, sh[r], color=PAL[r], lw=1.8, label=r)
shade_proj(ax); ax.set_ylabel("% of countries"); ax.set_title("Share of countries where |migration| > |natural change|", fontsize=10)
fig.tight_layout(); save(fig, "f16_migration.png")
NUM["mig_top"] = {"senders": (mig.head(5) / 1e3).round(2).to_dict(), "receivers": (mig.tail(5) / 1e3).round(2).to_dict()}
NUM["mig_dominant_share_2023"] = {r: round(float(sh.loc[2023, r]), 1) for r in REGION_ORDER}
NUM["mig_dominant_share_2100"] = {r: round(float(sh.loc[2100, r]), 1) for r in REGION_ORDER}
# Gulf sex-ratio signature
gulf = ["Qatar", "United Arab Emirates", "Oman", "Kuwait", "Bahrain", "Saudi Arabia"]
NUM["highest_sex_ratio_2023"] = c23.nlargest(6, "PopSexRatio")[["Location", "PopSexRatio", "CNMR"]].round(1).to_dict("records")
NUM["share_pop_growth_from_migration_2023"] = float((c23.CNMR / (c23.PopGrowthRate * 10).replace(0, np.nan)).abs().median())

# ============================================================ 7. sex differences
print("\n[7] sex differences")
df["LE_gap"] = df.LExFemale - df.LExMale
gap_reg = df.groupby(["Time", "Region"]).LE_gap.mean().unstack()[REGION_ORDER]
neg = df.groupby("Time").LE_gap.apply(lambda s: (s < 0).sum())
fig, axes = plt.subplots(1, 3, figsize=(17, 4.4))
for r in REGION_ORDER:
    axes[0].plot(gap_reg.index, gap_reg[r], color=PAL[r], lw=1.8, label=r)
shade_proj(axes[0]); axes[0].axhline(0, color="k", lw=.5); axes[0].set_title("Female - male life expectancy (mean gap, yrs)"); axes[0].legend(fontsize=7)
sns.histplot(df[df.Time == 2023].LE_gap, bins=30, ax=axes[1], color="#30638E", kde=True); axes[1].set_title("Gap distribution, 2023"); axes[1].set_xlabel("years")
axes[2].bar(neg.index, neg.values, color="#D1495B"); shade_proj(axes[2]); axes[2].set_title("Countries where men outlive women (count)")
fig.tight_layout(); save(fig, "f17_sex_gap.png")
NUM["le_gap_2023_mean"] = float(df[df.Time == 2023].LE_gap.mean())
NUM["neg_gap_total_rows"] = int((df.LE_gap < 0).sum())
NUM["neg_gap_by_decade"] = {int(k): int(v) for k, v in df.assign(dec=df.Time // 10 * 10).groupby("dec").LE_gap.apply(lambda s: (s < 0).sum()).items() if v > 0}
NUM["neg_gap_countries_top"] = df[df.LE_gap < 0].groupby("Location").size().sort_values(ascending=False).head(8).to_dict()

# ============================================================ 8. estimate / projection boundary
print("\n[8] estimate vs projection boundary")
d_ = df.sort_values(["LocID", "Time"]).copy()
for col in ["LEx", "TFR", "MedianAgePop", "PopGrowthRate"]:
    d_["d_" + col] = d_.groupby("LocID")[col].diff().abs()
bd = d_.groupby("Time")[[f"d_{c}" for c in ["LEx", "TFR", "MedianAgePop"]]].median()
fig, axes = plt.subplots(1, 3, figsize=(16, 4))
for ax, col in zip(axes, ["LEx", "TFR", "MedianAgePop"]):
    ax.plot(bd.index, bd[f"d_{col}"], color="#30638E"); shade_proj(ax); ax.set_title(f"Median |year-on-year change|: {LABEL[col]}", fontsize=10)
fig.tight_layout(); save(fig, "f18_estimate_projection_boundary.png")
bnd = {}
for col in ["LEx", "TFR", "MedianAgePop", "PopGrowthRate"]:
    a = d_[(d_.Time.between(2014, 2023))][f"d_{col}"].dropna(); b = d_[(d_.Time.between(2024, 2033))][f"d_{col}"].dropna()
    bnd[col] = {"median_abs_change_2014_23": round(float(a.median()), 4), "median_abs_change_2024_33": round(float(b.median()), 4),
                "mannwhitney_p": float(stats.mannwhitneyu(a, b).pvalue)}
NUM["boundary"] = bnd
# smoothness of projections: share of countries with monotone paths
def mono_share(col, lo, hi):
    g = df[df.Time.between(lo, hi)].sort_values("Time").groupby("LocID")[col]
    inc = g.apply(lambda s: (s.diff().dropna() >= -1e-9).all()); dec = g.apply(lambda s: (s.diff().dropna() <= 1e-9).all())
    return float((inc | dec).mean())
NUM["monotone_share_2024_2100"] = {c: round(mono_share(c, 2024, 2100), 3) for c in ["LEx", "TFR", "MedianAgePop", "TPopulation1Jan"]}
NUM["monotone_share_1950_2023"] = {c: round(mono_share(c, 1950, 2023), 3) for c in ["LEx", "TFR", "MedianAgePop", "TPopulation1Jan"]}

# ============================================================ 9. shocks & outliers
print("\n[9] shocks")
fl = df[df.flag_any_shock]
by_dec = fl.assign(dec=fl.Time // 10 * 10).groupby("dec")[["flag_mortality_shock", "flag_migration_shock", "flag_growth_extreme"]].sum()
fig, axes = plt.subplots(1, 3, figsize=(18, 4.8))
by_dec.plot.bar(stacked=True, ax=axes[0], color=["#D1495B", "#30638E", "#EDAE49"]); axes[0].set_title("Flagged country-years by decade"); axes[0].set_xlabel("")
axes[0].legend(["LEx drop >=3y", "|CNMR|>50", "|growth|>10%"], fontsize=8)
cnt = fl.groupby("Location").size().sort_values(ascending=False).head(12)
axes[1].barh(cnt.index[::-1], cnt.values[::-1], color="#7A9E7E"); axes[1].set_title("Countries with most flagged years"); axes[1].tick_params(axis="y", labelsize=8)
for loc, cc in [("Rwanda", "#D1495B"), ("Cambodia", "#EDAE49"), ("Central African Republic", "#30638E"), ("Somalia", "#7A9E7E"), ("Haiti", "#8E5572"), ("Ukraine", "k")]:
    d = df[df.Location == loc]; axes[2].plot(d.Time, d.LEx, color=cc, label=loc)
shade_proj(axes[2]); axes[2].set_title("Life expectancy shocks (kept, flagged)"); axes[2].legend(fontsize=7, ncol=2)
fig.tight_layout(); save(fig, "f19_shocks.png")
NUM["shock_counts"] = {c: int(df[c].sum()) for c in ["flag_mortality_shock", "flag_migration_shock", "flag_growth_extreme", "flag_any_shock"]}
NUM["shock_top_countries"] = cnt.head(8).to_dict()
NUM["shock_by_decade"] = by_dec.astype(int).to_dict()
fl_tab = fl[["Location", "Time", "LEx", "CNMR", "PopGrowthRate", "flag_mortality_shock", "flag_migration_shock", "flag_growth_extreme"]]
fl_tab.to_csv(TAB / "t09_flagged_shocks.csv", index=False)
NUM["shock_in_projection"] = int(fl.is_projection.sum())

# Central African Republic anomaly detail
car = df[df.Location == "Central African Republic"].set_index("Time").LEx
NUM["car_lex"] = {int(y): round(float(car.loc[y]), 1) for y in (2005, 2008, 2009, 2010, 2018, 2019, 2021, 2022, 2023)}
NUM["lex_min"] = df.nsmallest(3, "LEx")[["Location", "Time", "LEx"]].round(1).to_dict("records")

# ============================================================ 10. fertility transition timing
print("\n[10] fertility transition timing")
first_below = df[df.TFR < 2.1].groupby("Location").Time.min()
fb = df.drop_duplicates("Location").set_index("Location")[["Region", "SubRegion", "CoreCountry"]].join(first_below.rename("year_below_repl"))
never = int(fb.year_below_repl.isna().sum()); already50 = int((fb.year_below_repl == 1950).sum())
fig, axes = plt.subplots(1, 2, figsize=(15, 4.8))
axes[0].hist([fb[(fb.Region == r)].year_below_repl.dropna() for r in REGION_ORDER], bins=range(1950, 2105, 5),
             color=[PAL[r] for r in REGION_ORDER], label=REGION_ORDER, stacked=True)
axes[0].axvline(LAST_EST + .5, color="grey", ls="--"); axes[0].set_xlabel("First year TFR < 2.1 (replacement)"); axes[0].set_ylabel("Countries"); axes[0].legend(fontsize=8)
axes[0].set_title("When do countries cross below replacement fertility?")
nb = df.assign(b=df.TFR < 2.1).groupby("Time").apply(lambda g: pd.Series({"n": g.b.sum(), "popshare": g.loc[g.b, "TPopulation1July"].sum() / g.TPopulation1July.sum() * 100}))
axes[1].plot(nb.index, nb.popshare, color="k", lw=2, label="% of world population"); axes[1].set_ylabel("% of world population below replacement")
ax2 = axes[1].twinx(); ax2.plot(nb.index, nb.n, color="#D1495B", lw=1.5, ls="--"); ax2.set_ylabel("number of countries (dashed)", color="#D1495B"); ax2.grid(False)
shade_proj(axes[1]); axes[1].set_title("Spread of sub-replacement fertility")
fig.tight_layout(); save(fig, "f20_fertility_transition_timing.png")
NUM["tfr_below_repl"] = {"never_by_2100": never, "already_in_1950": already50,
                         "n_countries_2023": int(nb.loc[2023, "n"]), "popshare_2023": round(float(nb.loc[2023, "popshare"]), 1),
                         "popshare_2050": round(float(nb.loc[2050, "popshare"]), 1), "popshare_2100": round(float(nb.loc[2100, "popshare"]), 1),
                         "n_countries_2100": int(nb.loc[2100, "n"])}
NUM["never_below_repl"] = fb[fb.year_below_repl.isna()].index.tolist()
NUM["median_year_below_repl_by_region"] = fb.groupby("Region").year_below_repl.median().to_dict()
fb.to_csv(TAB / "t10_year_below_replacement.csv")

# ============================================================ 11. serial structure (modelling-relevant)
print("\n[11] serial structure")
res = []
for col in ["LEx", "TFR", "MedianAgePop", "TPopulation1Jan", "CBR", "CDR", "PopGrowthRate", "CNMR", "IMR"]:
    p = df.pivot(index="Time", columns="LocID", values=col)
    for nm, seg in [("1950-2023 (estimates)", p.loc[:2023]), ("2024-2100 (projection)", p.loc[2024:])]:
        dd = seg.diff().dropna(how="all")
        ac_lvl = seg.apply(lambda s: s.autocorr(1)).median()
        ac_d = dd.apply(lambda s: s.autocorr(1)).median()
        # linear-trend R2 per country, median
        r2 = seg.apply(lambda s: np.corrcoef(np.arange(len(s)), s)[0, 1] ** 2 if s.std() > 0 else np.nan).median()
        res.append({"indicator": col, "segment": nm, "median_lag1_autocorr_levels": ac_lvl, "median_lag1_autocorr_first_diff": ac_d, "median_linear_trend_R2": r2})
ser = pd.DataFrame(res); ser.to_csv(TAB / "t11_serial_structure.csv", index=False)
NUM["serial"] = ser.round(3).to_dict("records")

# ============================================================ 12. regional summary table
reg_tab = c23.groupby("Region").agg(countries=("LocID", "size"), pop_millions=("TPopulation1Jan", lambda s: s.sum() / 1e3),
                                    LEx_mean=("LEx", "mean"), TFR_mean=("TFR", "mean"), MedianAge_mean=("MedianAgePop", "mean"),
                                    IMR_median=("IMR", "median"), CNMR_median=("CNMR", "median")).reindex(REGION_ORDER).round(2)
reg_tab.to_csv(TAB / "t12_regional_summary_2023.csv")
sub_tab = c23.groupby(["Region", "SubRegion"]).agg(countries=("LocID", "size"), pop_millions=("TPopulation1Jan", lambda s: s.sum() / 1e3),
                                                   LEx=("LEx", "median"), TFR=("TFR", "median"), MedianAge=("MedianAgePop", "median")).round(2)
sub_tab.to_csv(TAB / "t13_subregional_summary_2023.csv")
NUM["region_counts"] = c23.groupby("Region").size().to_dict()
NUM["n_core"] = int(c23.CoreCountry.sum()); NUM["n_territories"] = int((~c23.CoreCountry).sum())
NUM["small_pop_n"] = int(c23.flag_small_pop.sum())
NUM["tfr_extremes_2023"] = {"lowest": c23.nsmallest(3, "TFR")[["Location", "TFR"]].round(2).to_dict("records"), "highest": c23.nlargest(3, "TFR")[["Location", "TFR"]].round(2).to_dict("records")}
NUM["lex_extremes_2023"] = {"lowest": c23.nsmallest(3, "LEx")[["Location", "LEx"]].round(1).to_dict("records"), "highest": c23.nlargest(3, "LEx")[["Location", "LEx"]].round(1).to_dict("records")}
NUM["median_age_extremes_2023"] = {"lowest": c23.nsmallest(3, "MedianAgePop")[["Location", "MedianAgePop"]].round(1).to_dict("records"), "highest": c23.nlargest(3, "MedianAgePop")[["Location", "MedianAgePop"]].round(1).to_dict("records")}
NUM["median_age_2100_extremes"] = df[df.Time == 2100].nlargest(3, "MedianAgePop")[["Location", "MedianAgePop"]].round(1).to_dict("records")

# small-population influence: do micro-states drive the outliers?
NUM["small_pop_share_of_shock_rows"] = float(df[df.flag_any_shock].flag_small_pop.mean())
NUM["small_pop_share_of_all_rows"] = float(df.flag_small_pop.mean())
NUM["territory_share_of_shock_rows"] = float((~df[df.flag_any_shock].CoreCountry).mean())

(TAB / "key_numbers.json").write_text(json.dumps(NUM, indent=2, default=str))
print("\nDONE. key numbers ->", TAB / "key_numbers.json")
