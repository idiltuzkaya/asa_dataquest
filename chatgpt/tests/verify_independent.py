"""Second implementation: standard library CSV + Decimal, no pandas or analyze import."""
import csv,gzip,json,hashlib
from decimal import Decimal as D
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; RAW=ROOT/'data/raw'
needed={'Medium','Momentum','Zero migration','Instant replacement zero migration','Instant replacement','Lower 95 PI','Upper 95 PI'}
values={}; base={}; tfr={}; countries=set(); rows=0
for fn in ['WPP2024_Demographic_Indicators_Medium_csv.gz','WPP2024_Demographic_Indicators_OtherVariants_csv.gz']:
 with gzip.open(RAW/fn,'rt',encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f):
   rows+=1; loc=int(r['LocID']); year=int(r['Time']); v=r['Variant']
   if r['ISO3_code']:
    countries.add(loc)
    if v=='Medium' and year==2023: tfr[loc]=D(r['TFR']) if r['TFR'] else None
   if v=='Medium' and year==2024: base[loc]=D(r['TPopulation1Jan'])
   if year in {2030,2050,2075,2100} and v in needed and r['TPopulation1Jan']:
    values[(loc,year,v)]=D(r['TPopulation1Jan'])
errors=[]; n=0; max_error=D('0')
with open(ROOT/'results/tables/scenario_decomposition.csv') as f:
 for r in csv.DictReader(f):
  l=int(r['LocID']); y=int(r['Time']); get=lambda v: values[(l,y,v)]
  expected={'momentum':get('Momentum')-base[l], 'mortality':get('Instant replacement zero migration')-get('Momentum'), 'fertility':get('Zero migration')-get('Instant replacement zero migration'), 'migration':get('Medium')-get('Zero migration'), 'total_change':get('Medium')-base[l]}
  assert sum(expected[k] for k in ['momentum','mortality','fertility','migration'])==expected['total_change']
  for k,x in expected.items():
   err=abs(D(r[k])-x); max_error=max(max_error,err); n+=1
   if err>D('.001'): errors.append((l,y,k,str(err)))
counts={}
for y in [2050,2075,2100]:
 low={l for l in countries if tfr.get(l) is not None and tfr[l]<D('2.1')}
 growing={l for l in low if values[l,y,'Medium']>base[l]}
 counts[str(y)]={'low_fertility':len(low),'low_and_growing':len(growing)}
summary=json.loads((ROOT/'results/summary.json').read_text())
for y,v in counts.items():
 r=next(x for x in summary['threshold_horizon_sensitivity'] if x['year']==int(y) and x['definition']=='TFR<2.1' and x['minimum_population_thousands']==0)
 assert all(v[k]==r[k] for k in v)
assert not errors,errors[:5]
result={'implementation':'Python csv/gzip/Decimal, no pandas, independent formula evaluation','raw_rows_streamed':rows,'numeric_comparisons':n,'max_csv_rounding_error_thousands':str(max_error),'counts':counts,'passed':True}
(ROOT/'results/independent_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
