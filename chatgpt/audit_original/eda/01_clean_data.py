"""
STEP 1 — Data cleaning pipeline for WPP2024 Demographic Indicators (Medium variant).

Run from the project root:
    uv run --with pandas --with numpy python eda/01_clean_data.py

Inputs  (data/):  WPP2024_Demographic_Indicators_Medium_csv.gz
                  WPP2024_Supplement_Births_and_LE60.csv
Outputs (data/clean/):
    wpp2024_countries_clean.csv   analysis panel: 237 countries x 1950-2100, region columns, flags
    wpp2024_aggregates.csv        non-country rows (World, regions, groupings) for reconciliation only
    country_regions.csv           ISO3-keyed Region / SubRegion lookup (validated)
Outputs (eda/tables/):
    cleaning_log.csv / cleaning_log.json   every cleaning decision with counts
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import region_mapping as rm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "WPP2024_Demographic_Indicators_Medium_csv.gz"
SUPP = ROOT / "data" / "WPP2024_Supplement_Births_and_LE60.csv"
OUT = ROOT / "data" / "clean"
TAB = ROOT / "eda" / "tables"
OUT.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

LAST_ESTIMATE_YEAR = 2023   # per Getting Started guide / supplement description: <=2023 estimates, >=2024 projections
LOG = []


def log(step, decision, before=None, after=None, detail=""):
    LOG.append({"step": step, "decision": decision, "rows_before": before, "rows_after": after, "detail": detail})
    print(f"[{step:>2}] {decision}  rows {before} -> {after}  {detail}")


# ------------------------------------------------------------------ 1. load
df = pd.read_csv(RAW, compression="gzip", encoding="utf-8-sig", low_memory=False)
log(1, "Load Medium file (utf-8-sig, gzip)", None, len(df), f"{df.shape[1]} columns")

# ------------------------------------------------------------------ 2. types
str_cols = [c for c in df.columns if df[c].dtype == "object" or str(df[c].dtype).startswith("str")]
for c in str_cols:
    df[c] = df[c].astype("string").str.strip()
df["Time"] = df["Time"].astype(int)
assert df["Variant"].nunique() == 1 and df["Variant"].iloc[0] == "Medium"
log(2, "Strip whitespace on text columns; Time -> int; verify Variant is constant 'Medium'", len(df), len(df),
    f"text cols: {str_cols}")

# ------------------------------------------------------------------ 3. duplicates
n_full = int(df.duplicated().sum())
n_key = int(df.duplicated(["LocID", "Time"]).sum())
assert n_full == 0 and n_key == 0
log(3, "Duplicate check (full-row and LocID x Time key)", len(df), len(df), f"full-row dups={n_full}, key dups={n_key}")

# ------------------------------------------------------------------ 4. location taxonomy
type_counts = df.groupby(df["LocTypeName"].fillna("<<unlabelled>>"))["LocID"].nunique().to_dict()
log(4, "Audit LocTypeName (aggregates + unlabelled groupings mixed with countries)", len(df), len(df),
    f"distinct locations per type: {type_counts}")

countries = df[(df["LocTypeName"] == "Country/Area") & df["ISO3_code"].notna()].copy()
aggs = df[~df.index.isin(countries.index)].copy()
aggs["LocTypeName"] = aggs["LocTypeName"].fillna("Unlabelled grouping")
assert countries["ISO3_code"].groupby(countries["LocID"]).nunique().max() == 1
log(5, "Split countries (LocTypeName=='Country/Area' AND ISO3 present) from aggregates; aggregates saved separately",
    len(df), len(countries), f"{countries.LocID.nunique()} countries/areas, {aggs.LocID.nunique()} aggregate/grouping locations")

# ------------------------------------------------------------------ 6. reconciliation (proves the filter is right)
world = df[df["LocTypeName"] == "World"].set_index("Time")
yrs = countries[countries.Time <= 2100].groupby("Time")[["TPopulation1Jan", "Births", "Deaths"]].sum()
max_gap = float(((yrs / world.loc[yrs.index, ["TPopulation1Jan", "Births", "Deaths"]]) - 1).abs().max().max())
naive = float(df[df.Time == 2023].TPopulation1Jan.sum() / world.loc[2023, "TPopulation1Jan"])
assert max_gap < 1e-5, max_gap
log(6, "Reconcile: sum of countries == World row (population, births, deaths), all years", len(countries), len(countries),
    f"max relative gap={max_gap:.2e}; naive sum over ALL rows in 2023 = {naive:.1f}x world (double counting avoided)")

# ------------------------------------------------------------------ 7. year 2101
n2101 = int((countries.Time == 2101).sum())
nn = countries[countries.Time == 2101].select_dtypes("number").notna().sum()
only = nn[nn > 0].index.tolist()
before = len(countries)
pop2101 = countries.loc[countries.Time == 2101, ["LocID", "TPopulation1Jan"]].rename(columns={"TPopulation1Jan": "Pop2101"})
countries = countries[countries.Time <= 2100].copy()
log(7, "Drop year 2101: only these numeric columns are populated -> " + ", ".join(only), before, len(countries),
    f"{n2101} rows removed; 1-Jan-2101 population kept as `Pop2101` lookup")

# ------------------------------------------------------------------ 8. panel balance
rows_per = countries.groupby("LocID").size()
assert rows_per.nunique() == 1
log(8, "Verify balanced panel", len(countries), len(countries),
    f"{rows_per.iloc[0]} years x {rows_per.shape[0]} countries")

# ------------------------------------------------------------------ 9. region columns
loc_all = df.drop_duplicates("LocID").set_index("LocID")
un_names = countries["Location"].drop_duplicates().tolist()
team = pd.DataFrame(rm.resolve_user_list(un_names))              # asserts complete & one-to-one
sub2reg = rm.subregion_to_region()

# UN hierarchy subregion for every country (fallback + cross-validation)
loc_c = loc_all.loc[countries.LocID.unique(), ["Location", "ISO3_code", "ParentID"]].copy()
loc_c["UN_SubRegion"] = loc_c["ParentID"].map(loc_all["Location"])
loc_c.loc[loc_c["ParentID"] == rm.UN_NORTHERN_AMERICA_PARENT_ID, "UN_SubRegion"] = "Northern America"
loc_c["UN_SubRegion"] = loc_c["UN_SubRegion"].replace(rm.UN_SUBREGION_TO_TEAM)
assert loc_c["UN_SubRegion"].notna().all(), loc_c[loc_c["UN_SubRegion"].isna()]
assert set(loc_c["UN_SubRegion"]) <= set(sub2reg), set(loc_c["UN_SubRegion"]) - set(sub2reg)

lookup = loc_c.reset_index().merge(team[["Location", "Region", "SubRegion", "team_name"]], on="Location", how="left")
in_team = lookup["SubRegion"].notna()
disagree = lookup[in_team & (lookup["SubRegion"] != lookup["UN_SubRegion"])]
lookup["RegionSource"] = np.where(in_team, "team_list", "un_hierarchy")
lookup["SubRegion"] = lookup["SubRegion"].fillna(lookup["UN_SubRegion"])
lookup["Region"] = lookup["SubRegion"].map(sub2reg)
lookup["CoreCountry"] = in_team                       # True = in the team's list (UN member / observer states)
assert lookup["Region"].notna().all()
n_team = int(in_team.sum())
log(9, "Create Region/SubRegion (team list primary; UN ParentID hierarchy for territories)", len(countries), len(countries),
    f"{n_team} countries from team list (all name-resolved), {len(lookup)-n_team} territories/dependencies via UN hierarchy; "
    f"team-vs-UN subregion disagreements: {len(disagree)} {disagree['Location'].tolist()}")
lookup[["LocID", "ISO3_code", "Location", "team_name", "Region", "SubRegion", "RegionSource", "CoreCountry", "UN_SubRegion"]] \
    .sort_values(["Region", "SubRegion", "Location"]).to_csv(OUT / "country_regions.csv", index=False)

countries = countries.merge(lookup[["LocID", "Region", "SubRegion", "RegionSource", "CoreCountry"]], on="LocID", how="left")
assert countries[["Region", "SubRegion"]].notna().all().all()

# ------------------------------------------------------------------ 10. supplement
sup = pd.read_csv(SUPP, encoding="utf-8-sig")
assert not sup.duplicated(["LocID", "Time"]).any() and sup.isna().sum().sum() == 0
n0 = len(countries)
countries = countries.merge(sup[["LocID", "Time", "BirthsMale", "BirthsFemale", "LE60", "LE60Male", "LE60Female"]],
                            on=["LocID", "Time"], how="left", validate="1:1")
assert len(countries) == n0
miss_sup = countries.loc[countries["LE60"].isna(), "Location"].unique().tolist()
chk = (countries.BirthsMale + countries.BirthsFemale - countries.Births).abs().max()
lo = countries[["LE60Male", "LE60Female"]].min(axis=1)
hi = countries[["LE60Male", "LE60Female"]].max(axis=1)
le_ok = ((countries.LE60 >= lo - 1.5e-3) & (countries.LE60 <= hi + 1.5e-3)) | countries.LE60.isna()
log(10, "Left-merge supplement (BirthsMale/Female, LE60 + sex) on LocID x Time; validate documented consistency", n0, len(countries),
    f"no supplement rows for {miss_sup}; max|M+F-Births|={chk:.4f}; LE60 within [male,female] violations={(~le_ok).sum()}")

# ------------------------------------------------------------------ 11. missing values
num = countries.select_dtypes("number").columns.difference(["LocID", "SortOrder", "LocTypeID", "ParentID", "VarID", "SDMX_code", "Time"])
miss = countries[num].isna().sum()
miss = miss[miss > 0]
dt = countries[countries.DoublingTime.isna()]
struct = int((dt.PopGrowthRate <= 0).sum())
capped = int((dt.PopGrowthRate > 0).sum())
log(11, "Missing-value audit (1950-2100)", len(countries), len(countries),
    f"columns with NaN: {miss.to_dict()}. DoublingTime NaN is STRUCTURAL: {struct} rows growth<=0 (undefined) + {capped} rows with "
    f"growth>0 but doubling time beyond the UN reporting cap (max observed={countries.DoublingTime.max():.1f} yrs). "
    f"Left as NaN, NOT imputed. Holy See has no supplement rows (documented).")

# ------------------------------------------------------------------ 12. range / logical validity
checks = {
    "negative population": int((countries[["TPopulation1Jan", "TPopulation1July"]] < 0).any(axis=1).sum()),
    "TFR<=0": int((countries.TFR <= 0).sum()),
    "LEx outside (0,100)": int(((countries.LEx <= 0) | (countries.LEx >= 100)).sum()),
    "Male+Female != Total (July, tol 0.01k)": int(((countries.TPopulationMale1July + countries.TPopulationFemale1July - countries.TPopulation1July).abs() > 0.01).sum()),
    "Births-Deaths != NatChange (tol 1e-6)": int(((countries.Births - countries.Deaths - countries.NatChange).abs() > 1e-6).sum()),
    "DeathsM+DeathsF != Deaths (tol 0.01k)": int(((countries.DeathsMale + countries.DeathsFemale - countries.Deaths).abs() > 0.01).sum()),
    "Q0040 > Q0060": int((countries.Q0040 > countries.Q0060).sum()),
    "IMR > Q5": int((countries.IMR > countries.Q5).sum()),
    "Births1519 > Births": int((countries.Births1519 > countries.Births).sum()),
    "Female LEx < Male LEx (plausible, kept)": int((countries.LExFemale < countries.LExMale).sum()),
}
assert all(v == 0 for k, v in checks.items() if "kept" not in k)
log(12, "Logical-validity checks (all demographic accounting identities hold)", len(countries), len(countries), json.dumps(checks))

# ------------------------------------------------------------------ 13. flags (nothing deleted)
countries = countries.sort_values(["LocID", "Time"]).reset_index(drop=True)
countries["is_projection"] = countries["Time"] > LAST_ESTIMATE_YEAR
countries["dLEx"] = countries.groupby("LocID")["LEx"].diff()
countries["flag_mortality_shock"] = countries["dLEx"] <= -3
countries["flag_migration_shock"] = countries["CNMR"].abs() > 50
countries["flag_growth_extreme"] = countries["PopGrowthRate"].abs() > 10
countries["flag_any_shock"] = countries[["flag_mortality_shock", "flag_migration_shock", "flag_growth_extreme"]].any(axis=1)
pop23 = countries.loc[countries.Time == 2023].set_index("LocID")["TPopulation1Jan"]
countries["flag_small_pop"] = countries["LocID"].map(pop23 < 100)         # < 100 thousand inhabitants in 2023
countries = countries.drop(columns=["dLEx"])
flag_counts = {c: int(countries[c].sum()) for c in ["is_projection", "flag_mortality_shock", "flag_migration_shock",
                                                    "flag_growth_extreme", "flag_any_shock", "flag_small_pop"]}
shock_locs = sorted(countries.loc[countries.flag_any_shock, "Location"].unique())
log(13, "Outliers FLAGGED not removed (real events: Rwanda 1994, Cambodia 1975-79, Kuwait 1990-91, Ukraine 2022 ...). "
        "Rules: LEx drop>=3y yoy | |CNMR|>50 per 1000 | |PopGrowthRate|>10%; small_pop = <100k people in 2023",
    len(countries), len(countries), f"flag row counts {flag_counts}; {len(shock_locs)} countries touched by >=1 shock flag")

# ------------------------------------------------------------------ 14. drop constant / redundant columns
drop = ["SortOrder", "LocTypeID", "LocTypeName", "ParentID", "VarID", "Variant", "SDMX_code"]
countries = countries.drop(columns=drop)
countries = countries.rename(columns={"Notes": "Footnote"})      # UN footnote key (text), not an indicator
countries["Footnote"] = countries["Footnote"].astype("string")
front = ["LocID", "ISO3_code", "ISO2_code", "Location", "Region", "SubRegion", "RegionSource", "CoreCountry", "Time",
         "is_projection", "Footnote"]
rest = [c for c in countries.columns if c not in front]
countries = countries[front + rest]
log(14, f"Drop constant/redundant columns {drop}; reorder", len(countries), len(countries), f"final shape {countries.shape}")

# ------------------------------------------------------------------ write
countries.to_csv(OUT / "wpp2024_countries_clean.csv", index=False)
aggs_out = aggs[aggs.Time <= 2100].drop(columns=["SortOrder", "LocTypeID", "VarID", "Variant", "SDMX_code", "ISO3_code", "ISO2_code"], errors="ignore")
aggs_out.to_csv(OUT / "wpp2024_aggregates.csv", index=False)
pop2101.to_csv(OUT / "pop_2101_lookup.csv", index=False)
pd.DataFrame(LOG).to_csv(TAB / "cleaning_log.csv", index=False)
(TAB / "cleaning_log.json").write_text(json.dumps(LOG, indent=2, default=str))
print(f"\nSaved: {OUT/'wpp2024_countries_clean.csv'}  shape={countries.shape}")
print(f"Saved: {OUT/'wpp2024_aggregates.csv'}  shape={aggs_out.shape}")
print(f"Saved: {OUT/'country_regions.csv'}")
