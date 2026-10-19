"""Run only after independent_freeze.json exists. Does not modify previous work."""
from pathlib import Path
import json,hashlib
import pandas as pd
import numpy as np
R=Path(__file__).resolve().parents[1]
# Support both the original sibling layout and chatgpt/ inside the published repository.
O=R.parent if (R.parent/'data/clean/wpp2024_countries_clean.csv').exists() else R.parent/'asa_dataquest'
T=R/'results/tables'
assert (R/'sources/independent_freeze.json').exists()
a=pd.read_csv(T/'country_panel.csv').set_index(['LocID','Time']).sort_index()
b=pd.read_csv(O/'data/clean/wpp2024_countries_clean.csv').set_index(['LocID','Time']).sort_index()
assert a.index.equals(b.index)
common=[x for x in a.select_dtypes('number').columns if x in b.columns and pd.api.types.is_numeric_dtype(b[x])]
comparison=[]
for k in common:
 diff=(a[k]-b[k]).abs()
 comparison.append({'column':k,'max_abs_difference':float(diff.max()),'missing_mismatches':int((a[k].isna()!=b[k].isna()).sum())})
pd.DataFrame(comparison).to_csv(T/'comparison_clean_values.csv',index=False)
# Compare geographical definitions after collapsing independent Americas split.
ar=a.Region.replace({'Northern America':'Americas','Latin America and the Caribbean':'Americas'})
regions_mismatch=int((ar!=b.Region).sum())
# Reproduce the prior analysis on its OWN endpoint (1 Jan 2101), independent of its code.
m=pd.read_csv(R/'data/raw/WPP2024_Demographic_Indicators_Medium_csv.gz',low_memory=False)
v=pd.read_csv(R/'data/raw/WPP2024_Demographic_Indicators_OtherVariants_csv.gz',usecols=['LocID','Time','Variant','TPopulation1Jan','TFR','NRR'],low_memory=False)
P=v[v.Time.eq(2101)&v.LocID.isin(a.index.get_level_values(0))].pivot(index='LocID',columns='Variant',values='TPopulation1Jan')
P['baseline']=m[m.Time.eq(2024)].set_index('LocID').TPopulation1Jan
P['Medium']=m[m.Time.eq(2101)].set_index('LocID').TPopulation1Jan
ind=pd.DataFrame({'momentum':np.log(P.Momentum/P.baseline),'mortality':np.log(P['Instant replacement zero migration']/P.Momentum),'fertility':np.log(P['Zero migration']/P['Instant replacement zero migration']),'migration':np.log(P.Medium/P['Zero migration']),'total':np.log(P.Medium/P.baseline)})
old=pd.read_csv(O/'analysis/tables/decomp_countries.csv').set_index('LocID')
numdiff=(ind-old[ind.columns]).abs().max().to_dict()
alt_incoherence=old.momentum+old.mortality_alt+old.fertility_alt+old.migration_alt-old.total
correct_alt=pd.DataFrame({'momentum':ind.momentum,'mortality':ind.mortality,'fertility':np.log(P.Medium/P['Instant replacement']),'migration':np.log(P['Instant replacement']/P['Instant replacement zero migration'])})
assert np.allclose(correct_alt.sum(axis=1),ind.total)
dom_main=ind.drop(columns='total').abs().idxmax(axis=1);dom_alt=correct_alt.abs().idxmax(axis=1)
migration_only=old[(old.migration>0)&(old.momentum<=0)&(old.fertility<=0)]
# Assert complete variant baselines match, independent of previous assertions.
base=m[m.Time.eq(2024)].set_index('LocID').TPopulation1Jan
b0=v[v.Time.eq(2024)&v.Variant.ne('Mean')].copy(); b0['base']=b0.LocID.map(base)
basediff=float((b0.TPopulation1Jan-b0.base).abs().max());assert basediff==0
# Independent EDA diagnostics for report claims.
c=m[m.ISO3_code.notna()&m.Time.le(2100)].sort_values(['LocID','Time']).copy(); c['dlex']=c.groupby('LocID').LEx.diff().abs()
lexsd=c.groupby('Time').LEx.std(); increases=lexsd.diff().gt(0)
weighted=[]
for year in [1950,2023,2100]:
 cc=c[c.Time.eq(year)]; world=m[m.LocID.eq(900)&m.Time.eq(year)].iloc[0]
 for k in ['TFR','MedianAgePop','LEx']:
  weighted.append({'year':year,'indicator':k,'population_weighted_country_average':float(np.average(cc[k],weights=cc.TPopulation1July)),'UN_world_indicator':float(world[k])})
pd.DataFrame(weighted).to_csv(T/'weighted_mean_vs_official_world.csv',index=False)
# Bytewise reproducibility of independently rerun legacy scripts in isolated copy.
rerun=[]
for folder in ['data/clean','eda/tables','analysis/tables']:
 for p in (O/folder).glob('*'):
  if p.suffix not in ['.csv','.json']:continue
  q=R/'audit_original'/folder/p.name
  rerun.append({'file':str(p.relative_to(O)),'rerun_exists':q.exists(),'identical_bytes':q.exists() and p.read_bytes()==q.read_bytes()})
# Small changes from floating-point/platform formatting are not automatically semantic errors.
summary={'independent_source_and_old_code_compared_after_freeze':True,'shared_numeric_columns':len(common),'numeric_value_comparisons':len(a)*len(common),'max_clean_numeric_difference':max(r['max_abs_difference'] for r in comparison),'missing_value_mismatches':sum(r['missing_mismatches'] for r in comparison),'region_row_mismatches_after_explicit_americas_collapse':regions_mismatch,'prior_log_decomposition_max_errors':numdiff,'variant_baseline_max_difference':basediff,'prior_alternative_chain_max_abs_log_residual':float(alt_incoherence.abs().max()),'prior_alternative_chain_worst_location':old.loc[alt_incoherence.abs().idxmax(),'Location'],'prior_reported_dominant_agreement':json.loads((O/'analysis/tables/decomp_numbers.json').read_text())['robustness_alt_path']['dominant_driver_unchanged_share'],'valid_swap_dominant_agreement':float((dom_main==dom_alt).mean()),'valid_swap_changed_locations':old.loc[dom_main.ne(dom_alt),'Location'].tolist(),'migration_only_claim_rows':len(migration_only),'of_these_positive_mortality_rows':int(migration_only.mortality.gt(0).sum()),'LEx_SD_increases_count':int(increases.sum()),'LEx_SD_first_increase_year':int(increases[increases].index[0]),'median_dLEx_full_historical':float(c.loc[c.Time.le(2023),'dlex'].median()),'median_dLEx_2014_2023':float(c.loc[c.Time.between(2014,2023),'dlex'].median()),'median_dLEx_2024_2033':float(c.loc[c.Time.between(2024,2033),'dlex'].median()),'rerun_legacy_tables':rerun}
(R/'results/comparison_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
# Raw inputs in old repo match competition originals.
rawcomp=[]
for p in (O/'data').glob('*csv*'):
 q=R/'data/raw'/p.name
 if q.exists():rawcomp.append({'file':p.name,'identical_sha256':hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(q.read_bytes()).digest()})
(R/'results/prior_raw_comparison.json').write_text(json.dumps(rawcomp,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='rerun_legacy_tables'},indent=2,ensure_ascii=False));print('Rerun tables:',len(rerun),'exact:',sum(x['identical_bytes'] for x in rerun))
