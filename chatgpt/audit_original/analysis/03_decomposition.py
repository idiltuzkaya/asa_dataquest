"""
STEP 3 — Why will each country grow or shrink? Decomposing 2024-2100 population change into
momentum (today's age structure), fertility, mortality and migration.

Run from the project root (after eda/01_clean_data.py):
    .venv/bin/python analysis/03_decomposition.py

Method (Andreev, Kantorova & Bongaarts 2013, UN Population Division Technical Paper 2013/3), using the
UN's own counterfactual projection variants. All runs start from the same 1 Jan 2024 population P0 and end
on 1 Jan 2101 (end of 2100):
    Momentum run  (MOM) : replacement fertility, constant mortality, zero migration -> age structure only
    IRZM run            : replacement fertility, projected mortality, zero migration
    Zero migration (ZM) : projected fertility,   projected mortality, zero migration
    Medium        (MED) : projected fertility,   projected mortality, projected migration
Telescoping identity (exact, no residual):
    MED/P0 = (MOM/P0) * (IRZM/MOM) * (ZM/IRZM) * (MED/ZM)
           = momentum * mortality * fertility * migration
We work with natural logs so the four effects ADD UP to ln(MED/P0).

Robustness: the chain order is a choice. Each effect is re-estimated along a second path that the UN
variants also allow (fertility = MED/Instant replacement, mortality = MED/Constant mortality,
migration = Instant replacement/IRZM) and the agreement is reported.

Uncertainty: width of the UN 95% probabilistic interval in 2100, ln(Upper95/Lower95).

Outputs: analysis/tables/*.csv, analysis/tables/decomp_numbers.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TAB = ROOT / "analysis" / "tables"
TAB.mkdir(parents=True, exist_ok=True)

T0, T1 = 2024, 2101          # 1 Jan 2024 -> 1 Jan 2101 (= end of 2100)
VARIANTS = {"Momentum": "MOM", "Instant replacement zero migration": "IRZM", "Zero migration": "ZM",
            "Instant replacement": "IR", "Constant mortality": "CM", "High": "HIGH", "Low": "LOW",
            "Constant fertility": "CF", "Upper 95 PI": "U95", "Lower 95 PI": "L95", "Upper 80 PI": "U80",
            "Lower 80 PI": "L80"}
EFFECTS = ["momentum", "mortality", "fertility", "migration"]
NUM = {}

# ------------------------------------------------------------------ load
regions = pd.read_csv(DATA / "clean" / "country_regions.csv")
panel = pd.read_csv(DATA / "clean" / "wpp2024_countries_clean.csv",
                    usecols=["LocID", "Location", "ISO3_code", "Region", "SubRegion", "CoreCountry", "Time", "TFR",
                             "MedianAgePop", "NRR", "TPopulation1July", "CNMR", "NatChangeRT"])
countries = set(regions.LocID)

med = pd.read_csv(DATA / "WPP2024_Demographic_Indicators_Medium_csv.gz", encoding="utf-8-sig", low_memory=False,
                  usecols=["LocID", "Time", "TPopulation1Jan"])
med = med[med.LocID.isin(countries) & med.Time.isin([T0, T1])].pivot(index="LocID", columns="Time", values="TPopulation1Jan")
ov = pd.read_csv(DATA / "WPP2024_Demographic_Indicators_OtherVariants_csv.gz", encoding="utf-8-sig", low_memory=False,
                 usecols=["LocID", "Variant", "Time", "TPopulation1Jan"])
ov = ov[ov.LocID.isin(countries) & ov.Variant.isin(VARIANTS)]

# P[run] = population on 1 Jan 2101 (thousands); P0 = 1 Jan 2024
P = ov[ov.Time == T1].pivot(index="LocID", columns="Variant", values="TPopulation1Jan").rename(columns=VARIANTS)
P["MED"] = med[T1]
P["P0"] = med[T0]
base = ov[ov.Time == T0].pivot(index="LocID", columns="Variant", values="TPopulation1Jan")
assert (base.sub(P["P0"], axis=0).abs().max().max()) == 0, "all variants must start from the same 2024 population"
assert P.notna().all().all() and len(P) == 237
assert (P.drop(columns=["L95", "L80"]) > 0).all().all()
# UN probabilistic lower bounds hit exactly 0 for a few migration-driven places -> log width undefined, set NaN
NUM["pi_lower_bound_zero"] = {v: P.index[P[v] <= 0].map(dict(zip(regions.LocID, regions.Location))).tolist() for v in ["L95", "L80"]}
P[["L95", "L80"]] = P[["L95", "L80"]].where(P[["L95", "L80"]] > 0)


def decompose(p):
    """p: DataFrame/Series with columns P0, MOM, IRZM, ZM, MED -> log effects (sum == ln(MED/P0))."""
    out = pd.DataFrame({
        "momentum": np.log(p["MOM"] / p["P0"]),
        "mortality": np.log(p["IRZM"] / p["MOM"]),
        "fertility": np.log(p["ZM"] / p["IRZM"]),
        "migration": np.log(p["MED"] / p["ZM"]),
    })
    out["total"] = np.log(p["MED"] / p["P0"])
    assert np.allclose(out[EFFECTS].sum(axis=1), out["total"]), "telescoping identity broken"
    return out


# ------------------------------------------------------------------ country decomposition
D = decompose(P).join(regions.set_index("LocID")[["Location", "ISO3_code", "Region", "SubRegion", "CoreCountry"]])
D = D.join(P[["P0", "MED", "MOM", "IRZM", "ZM"]].rename(columns=lambda c: f"pop_{c}"))
x24 = panel[panel.Time == T0].set_index("LocID")
D["TFR2024"], D["MedianAge2024"], D["NRR2024"] = x24.TFR, x24.MedianAgePop, x24.NRR
D["growth_pct"] = (np.exp(D.total) - 1) * 100
# dominant driver = effect with the largest absolute log contribution
D["dominant"] = D[EFFECTS].abs().idxmax(axis=1)
dom_val = D[EFFECTS].to_numpy()[np.arange(len(D)), D[EFFECTS].abs().to_numpy().argmax(1)]
D["dominant_signed"] = D["dominant"] + np.where(dom_val > 0, " (+)", " (-)")

# robustness: alternative-path effects
alt = pd.DataFrame({
    "fertility_alt": np.log(P.MED / P.IR),          # fertility effect with migration and projected mortality present
    "mortality_alt": np.log(P.MED / P.CM),          # mortality effect with projected fertility and migration present
    "migration_alt": np.log(P.IR / P.IRZM),         # migration effect at replacement fertility
})
D = D.join(alt)
rob = {}
for e in ["fertility", "mortality", "migration"]:
    a, b = D[e], D[f"{e}_alt"]
    rob[e] = {"spearman": round(float(stats.spearmanr(a, b)[0]), 3), "pearson": round(float(np.corrcoef(a, b)[0, 1]), 3),
              "median_abs_diff_log": round(float((a - b).abs().median()), 4),
              "sign_agreement": round(float((np.sign(a) == np.sign(b)).mean()), 3)}
rob["dominant_driver_unchanged_share"] = round(float(
    (D[EFFECTS].abs().idxmax(axis=1) ==
     D[["momentum", "mortality_alt", "fertility_alt", "migration_alt"]].abs().idxmax(axis=1).str.replace("_alt", "")).mean()), 3)
NUM["robustness_alt_path"] = rob

# ------------------------------------------------------------------ aggregates (sum runs, then decompose)
def agg_decomp(by):
    s = P.join(regions.set_index("LocID")[["Region", "SubRegion"]]).groupby(by)[["P0", "MOM", "IRZM", "ZM", "MED"]].sum() \
        if by else P[["P0", "MOM", "IRZM", "ZM", "MED"]].sum().to_frame("World").T
    return decompose(s).join(s)


W = agg_decomp(None)
R = agg_decomp("Region")
S = agg_decomp("SubRegion")
NUM["world"] = {k: round(float(v), 4) for k, v in W.iloc[0].items()}
NUM["world_factors"] = {e: round(float(np.exp(W[e].iloc[0])), 3) for e in EFFECTS + ["total"]}
NUM["region_factors"] = {r: {e: round(float(np.exp(R.loc[r, e])), 3) for e in EFFECTS + ["total"]} for r in R.index}
NUM["region_growth_pct"] = (np.exp(R.total) - 1).mul(100).round(1).to_dict()
# additive split of the world's absolute change (people) in proportion to log effects
W_change_bn = (W.MED.iloc[0] - W.P0.iloc[0]) / 1e6
NUM["world_change_bn"] = round(float(W_change_bn), 3)
NUM["world_P0_bn"], NUM["world_2101_bn"] = round(float(W.P0.iloc[0] / 1e6), 3), round(float(W.MED.iloc[0] / 1e6), 3)
NUM["world_momentum_only_bn"] = round(float(W.MOM.iloc[0] / 1e6), 3)

# ------------------------------------------------------------------ headline facts
n = len(D)
popw = D.pop_P0 / D.pop_P0.sum()
NUM["n_countries"] = n
NUM["dominant_counts"] = D.dominant.value_counts().to_dict()
NUM["dominant_popshare_pct"] = (popw.groupby(D.dominant).sum() * 100).round(1).to_dict()
NUM["dominant_signed_counts"] = D.dominant_signed.value_counts().to_dict()
NUM["shrinking_n"] = int((D.total < 0).sum())
NUM["shrinking_popshare_pct"] = round(float(popw[D.total < 0].sum() * 100), 1)
NUM["momentum_positive_n"] = int((D.momentum > 0).sum())
NUM["momentum_positive_popshare_pct"] = round(float(popw[D.momentum > 0].sum() * 100), 1)

# "TFR alone misleads": already below replacement in 2024 yet locked into growth by age structure
sub = D[D.TFR2024 < 2.1]
NUM["below_repl_2024_n"] = len(sub)
NUM["below_repl_but_momentum_pos_n"] = int((sub.momentum > 0).sum())
NUM["below_repl_but_momentum_pos_pop_bn"] = round(float(sub.loc[sub.momentum > 0, "pop_P0"].sum() / 1e6), 2)
NUM["below_repl_but_grows_2024_2100_n"] = int((sub.total > 0).sum())
NUM["below_repl_but_grows_examples"] = sub[sub.total > 0].nlargest(8, "pop_P0")[["Location", "TFR2024", "growth_pct"]].round(2).to_dict("records")
# opposite: above replacement but shrinking (emigration)
sup = D[D.TFR2024 >= 2.1]
NUM["above_repl_but_shrinks"] = sup[sup.total < 0][["Location", "TFR2024", "growth_pct", "migration"]].round(2).to_dict("records")
# migration as the only positive force
mig_only = D[(D.migration > 0) & (D.momentum <= 0) & (D.fertility <= 0)]
NUM["migration_only_positive_n"] = len(mig_only)
NUM["migration_turns_decline_to_growth_n"] = int(((D.total - D.migration < 0) & (D.total > 0)).sum())
NUM["migration_offsets_natural_decline"] = D[(D.migration > 0) & (D.total - D.migration < 0) & (D.total > 0)] \
    .nlargest(10, "pop_P0")[["Location", "growth_pct"]].round(1).to_dict("records")

# correlation of single indicators with total growth (does any one indicator tell the whole story?)
NUM["spearman_total_vs"] = {c: round(float(stats.spearmanr(D[c], D.total)[0]), 3)
                            for c in ["TFR2024", "MedianAge2024", "momentum", "fertility", "migration", "mortality"]}
# variance share of each effect in the cross-country variance of total log growth: cov(e, total)/var(total) -> sums to 1
vt = D.total.var()
NUM["variance_share_of_total"] = {e: round(float(D[e].cov(D.total) / vt), 3) for e in EFFECTS}
NUM["variance_share_of_total_popweighted"] = {e: round(float(np.cov(D[e], D.total, aweights=D.pop_P0)[0, 1] /
                                                             np.cov(D.total, D.total, aweights=D.pop_P0)[0, 1]), 3) for e in EFFECTS}

# ------------------------------------------------------------------ uncertainty
D["pi95_logwidth"] = np.log(P.U95 / P.L95)
D["pi80_logwidth"] = np.log(P.U80 / P.L80)
D["hilo_logwidth"] = np.log(P.HIGH / P.LOW)           # deterministic +/- half-child fertility scenarios
D["cf_vs_med_log"] = np.log(P.CF / P.MED)              # what if fertility stays at today's level
D["pi95_ratio"] = P.U95 / P.L95
NUM["pi95_ratio_quantiles"] = D.pi95_ratio.describe(percentiles=[.1, .5, .9]).round(2).to_dict()
NUM["pi95_by_region_median_ratio"] = D.groupby("Region").pi95_ratio.median().round(2).to_dict()
NUM["pi95_widest"] = D[D.CoreCountry].nlargest(8, "pi95_ratio")[["Location", "pi95_ratio"]].round(2).to_dict("records")
NUM["pi95_narrowest"] = D[D.CoreCountry].nsmallest(5, "pi95_ratio")[["Location", "pi95_ratio"]].round(2).to_dict("records")
NUM["spearman_pi95_vs"] = {c: round(float(stats.spearmanr(D[c].abs() if c in EFFECTS else D[c], D.pi95_logwidth, nan_policy="omit")[0]), 3)
                           for c in ["momentum", "fertility", "migration", "mortality", "TFR2024", "MedianAge2024", "hilo_logwidth"]}
NUM["spearman_pi95_vs_logpop"] = round(float(stats.spearmanr(np.log(D.pop_P0), D.pi95_logwidth, nan_policy="omit")[0]), 3)
NUM["spearman_pi95_vs_logpop_p"] = float(stats.spearmanr(np.log(D.pop_P0), D.pi95_logwidth, nan_policy="omit")[1])
# world scenario paths (UN World row; country PI bounds do NOT sum to the world bound, so use the UN's own world PI)
wov = pd.read_csv(DATA / "WPP2024_Demographic_Indicators_OtherVariants_csv.gz", encoding="utf-8-sig", low_memory=False,
                  usecols=["LocTypeName", "Variant", "Time", "TPopulation1Jan"])
wov = wov[wov.LocTypeName == "World"].pivot(index="Time", columns="Variant", values="TPopulation1Jan") / 1e6
wmed = pd.read_csv(DATA / "WPP2024_Demographic_Indicators_Medium_csv.gz", encoding="utf-8-sig", low_memory=False,
                   usecols=["LocTypeName", "Time", "TPopulation1Jan"])
wmed = wmed[wmed.LocTypeName == "World"].set_index("Time").TPopulation1Jan / 1e6
wov = wov.reindex(wmed.index)
wov["Medium"] = wmed
wov.loc[1950:].to_csv(TAB / "world_scenarios_bn.csv")
pd.DataFrame({"Medium": wmed}).to_csv(TAB / "world_medium_1950_2101_bn.csv")
for col, run in [("MOM", "Momentum"), ("IRZM", "Instant replacement zero migration"), ("ZM", "Zero migration"), ("MED", "Medium")]:
    assert abs(W[col].iloc[0] / 1e6 - wov.loc[T1, run]) < 1e-3, f"country sum != UN World row for {run}"
NUM["world_2101_bn_by_run"] = wov.loc[T1].round(3).to_dict()
NUM["world_medium_peak"] = {"year": int(wmed.idxmax()), "bn": round(float(wmed.max()), 3)}
# OLS: what explains forecast uncertainty? (descriptive, HC3 robust SE)
import statsmodels.formula.api as smf
m = smf.ols("pi95_logwidth ~ TFR2024 + I(migration.abs()) + np.log(pop_P0)", data=D).fit(cov_type="HC3")
NUM["ols_pi95"] = {"params": m.params.round(4).to_dict(), "p": m.pvalues.round(5).to_dict(), "r2": round(float(m.rsquared), 3), "n": int(m.nobs)}
m2 = smf.ols("pi95_logwidth ~ TFR2024 + I(migration.abs()) + np.log(pop_P0) + C(Region)", data=D).fit(cov_type="HC3")
NUM["ols_pi95_region_fe"] = {"params": m2.params.round(4).to_dict(), "r2": round(float(m2.rsquared), 3)}

# ------------------------------------------------------------------ focus countries for slides
focus = ["Nigeria", "India", "China", "United States of America", "Germany", "Japan", "Republic of Korea", "Brazil",
         "Pakistan", "Türkiye", "Italy", "Ukraine", "Ethiopia", "Democratic Republic of the Congo", "Bangladesh",
         "Indonesia", "Egypt", "Russian Federation", "Mexico", "Philippines", "Viet Nam", "Iran (Islamic Republic of)",
         "United Kingdom", "Canada", "Australia", "Niger", "Somalia", "Poland", "Spain", "Thailand"]
F = D[D.Location.isin(focus)].sort_values("pop_P0", ascending=False)
assert len(F) == len(focus), set(focus) - set(F.Location)
NUM["focus"] = {r.Location: {"growth_pct": round(r.growth_pct, 1), **{e: round(float(np.exp(getattr(r, e))), 3) for e in EFFECTS},
                             "TFR2024": round(r.TFR2024, 2), "pi95_ratio": round(r.pi95_ratio, 2)} for r in F.itertuples()}

# ------------------------------------------------------------------ write
D.reset_index().to_csv(TAB / "decomp_countries.csv", index=False)
pd.concat([W.assign(level="World"), R.assign(level="Region"), S.assign(level="SubRegion")]).rename_axis("name") \
    .reset_index().to_csv(TAB / "decomp_aggregates.csv", index=False)
(TAB / "decomp_numbers.json").write_text(json.dumps(NUM, indent=2, default=str, ensure_ascii=False))
print(json.dumps(NUM, indent=1, default=str, ensure_ascii=False))
