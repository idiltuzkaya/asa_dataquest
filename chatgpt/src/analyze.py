"""Independent WPP2024 analysis. Written before inspecting prior analysis code.
All stocks are thousands of people; scenario decomposition uses 1 Jan 2024
and 1 Jan of target year, never mixing January and July populations.
"""
from pathlib import Path
import hashlib, json, sys, platform
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'; TAB=ROOT/'results/tables'; FIG=ROOT/'results/figures'
for p in (TAB,FIG): p.mkdir(parents=True,exist_ok=True)
checks=[]
def check(name, ok, detail):
    checks.append(dict(check=name,passed=bool(ok),detail=detail))
    if not ok: raise AssertionError(f'{name}: {detail}')
def save(df,name): df.to_csv(TAB/f'{name}.csv',index=False,float_format='%.10g')
def maxabs(s): return float(s.abs().max())
def num(df,cols):
    for c in cols:
        old=df[c]; new=pd.to_numeric(old,errors='coerce')
        bad=old.notna() & new.isna()
        check('numeric_parse_'+c,not bad.any(),{'unparseable':int(bad.sum())})
        df[c]=new
    return df

m=pd.read_csv(RAW/'WPP2024_Demographic_Indicators_Medium_csv.gz',encoding='utf-8-sig',low_memory=False)
metadata=list(m.columns[:13]); indicators=list(m.columns[13:]); m=num(m,indicators)
check('medium_dimensions',m.shape==(84360,67),list(m.shape))
check('medium_unique',not m.duplicated(['LocID','Time','Variant']).any(),'LocID, Time, Variant')
check('medium_variant',set(m.Variant)=={'Medium'},m.Variant.unique().tolist())
iso=m.ISO3_code.notna(); country=m.LocTypeName.eq('Country/Area')
check('country_filters_agree',iso.equals(country),{'iso_rows':int(iso.sum()),'type_rows':int(country.sum())})
check('country_count',m.loc[iso,'LocID'].nunique()==237,int(m.loc[iso,'LocID'].nunique()))
check('panel_complete',m.loc[iso].groupby('LocID').Time.nunique().eq(152).all(),'237 x 152, including 2101 boundary')
check('terminal_year_only_january',m.loc[m.Time.eq(2101),indicators[1:]].isna().all().all(),'Other 53 indicators absent in 2101')
meta=m.loc[m.Time.eq(2023),metadata].set_index('LocID')
REGIONS={903:'Africa',935:'Asia',908:'Europe',904:'Latin America and the Caribbean',905:'Northern America',909:'Oceania'}
def region(loc):
    # Raw parent 918 is absent. Its five children are the M49 Northern America members.
    # Map only this verified orphan and reconcile regional sums below.
    if loc == 918: return REGIONS[905]
    seen=set()
    while loc not in REGIONS:
        if loc in seen or loc not in meta.index: raise ValueError(f'Unresolved parent: {loc}')
        seen.add(loc); loc=int(meta.loc[loc,'ParentID'])
        if loc == 918: return REGIONS[905]
    return REGIONS[loc]
cm=meta.loc[meta.ISO3_code.notna(),['ISO3_code','Location','ParentID']].copy()
cm['Region']=[region(i) for i in cm.index]
save(cm.reset_index(),'country_regions')
c=m.loc[iso & m.Time.le(2100)].copy().sort_values(['LocID','Time'])
c['Region']=c.LocID.map(cm.Region); c['Period']=np.where(c.Time.le(2023),'Estimate','Projection')
check('country_year_unique',not c.duplicated(['LocID','Time']).any(),len(c))
save(c.groupby('Period')[indicators].agg(lambda s:int(s.isna().sum())).reset_index(),'missing_by_period')
save(c.groupby('LocID')[indicators].agg(lambda s:int(s.isna().sum())).reset_index(),'missing_by_country')
save(pd.DataFrame({'column':indicators,'missing':c[indicators].isna().sum().values,'min':c[indicators].min().values,'max':c[indicators].max().values}),'indicator_profile')
world=m.loc[m.LocID.eq(900)&m.Time.le(2100)].set_index('Time')
rec=c.groupby('Time').TPopulation1July.sum().to_frame('country_sum').join(world.TPopulation1July.rename('UN_world'))
rec['difference_thousands']=rec.country_sum-rec.UN_world
check('world_population_reconciles',maxabs(rec.difference_thousands)<0.03,maxabs(rec.difference_thousands))
save(rec.reset_index(),'world_reconciliation')
reg=c.groupby(['Region','Time']).TPopulation1July.sum().reset_index()
reg['share_world']=reg.TPopulation1July/reg.Time.map(world.TPopulation1July)
save(reg,'region_population')
for rid,rname in REGIONS.items():
    observed=reg[reg.Region.eq(rname)].set_index('Time').TPopulation1July
    expected=m[m.LocID.eq(rid)&m.Time.le(2100)].set_index('Time').TPopulation1July
    check('region_reconciles_'+rname,maxabs(observed-expected)<.03,maxabs(observed-expected))
# Annual bookkeeping: Jan(t+1)-Jan(t) and annual flows.
stock=m.loc[iso].set_index(['LocID','Time']).TPopulation1Jan
next_stock=pd.Series([stock.get((int(l),int(t)+1),np.nan) for l,t in zip(c.LocID,c.Time)],index=c.index)
res=pd.DataFrame({'LocID':c.LocID,'Time':c.Time,'natural_residual':c.NatChange-(c.Births-c.Deaths),'flow_residual':c.PopChange-(c.Births-c.Deaths+c.NetMigrations),'stock_residual':next_stock-c.TPopulation1Jan-c.PopChange,'sex_residual':c.TPopulation1July-c.TPopulationMale1July-c.TPopulationFemale1July})
for key in ['natural_residual','stock_residual','sex_residual']:
    check(key,maxabs(res[key])<0.004,{'max_abs_thousands':maxabs(res[key]),'nonmissing':int(res[key].notna().sum())})
save(res,'annual_identity_residuals')
flow_summary={'max_abs_thousands':maxabs(res.flow_residual),'median_abs_thousands':float(res.flow_residual.abs().median()),'rows_above_4_people':int(res.flow_residual.abs().gt(.004+1e-9).sum()),'interpretation':'Source flows do not close exactly. Residual is retained, not forced to zero; reason not established.'}
(ROOT/'results/flow_residual_warning.json').write_text(json.dumps(flow_summary,indent=2))
save(res.assign(abs_flow=res.flow_residual.abs()).nlargest(20,'abs_flow').merge(cm.reset_index()[['LocID','Location']],on='LocID'),'largest_flow_residuals')
# Supplement is absent for Holy See. No imputation or synthetic replacement.
s=pd.read_csv(RAW/'WPP2024_Supplement_Births_and_LE60.csv')
check('supplement_unique',not s.duplicated(['LocID','Time']).any(),len(s))
check('supplement_coverage',len(s)==236*151 and s.LocID.nunique()==236,len(s))
merged=c.merge(s[['LocID','Time','BirthsMale','BirthsFemale','LE60','LE60Male','LE60Female']],on=['LocID','Time'],how='left',validate='one_to_one',indicator=True)
missing=merged.loc[merged._merge.eq('left_only'),'Location'].unique().tolist()
check('supplement_missing_only_holy_see',missing==['Holy See'],missing)
check('supplement_births',maxabs(merged.Births-merged.BirthsMale-merged.BirthsFemale)<0.00101,maxabs(merged.Births-merged.BirthsMale-merged.BirthsFemale))
check('supplement_LE60_between_sexes',s.LE60.between(s[['LE60Male','LE60Female']].min(axis=1)-1e-9,s[['LE60Male','LE60Female']].max(axis=1)+1e-9).all(),'all supplement rows')
# Compact analysis panel, preserving original units and missingness.
save(merged.drop(columns='_merge'),'country_panel')

vcols=['LocID','ISO3_code','Location','Variant','Time','TPopulation1Jan','TPopulation1July','TFR','NRR','LEx','NetMigrations']
v=pd.read_csv(RAW/'WPP2024_Demographic_Indicators_OtherVariants_csv.gz',usecols=vcols,low_memory=False)
v=num(v,vcols[5:])
check('variants_unique',not v.duplicated(['LocID','Time','Variant']).any(),len(v))
check('variants_count',len(v)==662919 and v.Variant.nunique()==18,{'rows':len(v),'variants':v.Variant.nunique()})
save(v.groupby('Variant').agg(rows=('Time','size'),locations=('LocID','nunique'),first_year=('Time','min'),last_year=('Time','max'),jan_pop_nonmissing=('TPopulation1Jan','count'),july_pop_nonmissing=('TPopulation1July','count')).reset_index(),'variant_coverage')
allpop=pd.concat([m[vcols],v],ignore_index=True)
base=m.loc[m.Time.eq(2024)].set_index('LocID').TPopulation1Jan
chosen=['Medium','Zero migration','Instant replacement zero migration','Momentum','Instant replacement','High','Low','Lower 80 PI','Upper 80 PI','Lower 95 PI','Upper 95 PI','Median PI','Constant fertility','Constant mortality']
p=allpop.loc[allpop.Variant.isin(chosen)&allpop.Time.ge(2024)].pivot(index=['LocID','Time'],columns='Variant',values='TPopulation1Jan')
check('four_scenarios_complete',p[['Medium','Zero migration','Instant replacement zero migration','Momentum']].notna().all().all(),'555 locations x 78 years')
d=p.reset_index(); d['baseline']=d.LocID.map(base)
d['momentum']=d.Momentum-d.baseline
d['mortality']=d['Instant replacement zero migration']-d.Momentum
d['fertility']=d['Zero migration']-d['Instant replacement zero migration']
d['migration']=d.Medium-d['Zero migration']
d['total_change']=d.Medium-d.baseline
components=['momentum','mortality','fertility','migration']
d['reconstruction_residual']=d[components].sum(axis=1)-d.total_change
check('decomposition_reconstructs',maxabs(d.reconstruction_residual)<1e-6,maxabs(d.reconstruction_residual))
# Interaction sensitivity: changing the fertility/migration ordering.
d['migration_replacement_path']=d['Instant replacement']-d['Instant replacement zero migration']
d['fertility_with_migration_path']=d.Medium-d['Instant replacement']
d['fertility_migration_interaction']=d.migration-d.migration_replacement_path
check('alternative_path_reconstructs',maxabs(d.migration_replacement_path+d.fertility_with_migration_path-d.migration-d.fertility)<1e-6,'fertility/migration swapped')
for key in components+['total_change','fertility_migration_interaction']:
    d[key+'_pct_base']=100*d[key]/d.baseline
for col in ['Location','ISO3_code']:
    d[col]=d.LocID.map(meta[col])
d['Region']=d.LocID.map(cm.Region)
# Finite horizon momentum is a scenario contrast, not an inevitable amount of growth.
save(d.loc[d.Time.isin([2030,2050,2075,2100])],'scenario_decomposition')
save(d.loc[d.LocID.isin([900,792,156,356,566,392,276,840])],'selected_scenario_trajectories')
# Below-replacement definitions: fixed TFR cutoff and NRR, with denominator reported.
b2023=c[c.Time.eq(2023)].set_index('LocID')
classifications=[]
for year in [2050,2075,2100]:
    t=d.loc[d.Time.eq(year)&d.LocID.isin(cm.index)].copy().set_index('LocID')
    t=t.join(b2023[['TFR','NRR','TPopulation1July']].rename(columns={'TPopulation1July':'pop_2023'}))
    for threshold in [2.0,2.1,2.2]:
        for min_pop in [0,1000]:
            eligible=t.TFR.notna() & t.pop_2023.ge(min_pop)
            low=eligible & t.TFR.lt(threshold); growing=t.total_change.gt(0)
            classifications.append(dict(year=year,definition=f'TFR<{threshold}',minimum_population_thousands=min_pop,eligible=int(eligible.sum()),low_fertility=int(low.sum()),low_and_growing=int((low&growing).sum()),low_and_growing_share=float((low&growing).sum()/low.sum()),population_weighted_growing_share=float(t.loc[low&growing,'pop_2023'].sum()/t.loc[low,'pop_2023'].sum())))
    low=t.NRR.lt(1); eligible=t.NRR.notna()
    classifications.append(dict(year=year,definition='NRR<1',minimum_population_thousands=0,eligible=int(eligible.sum()),low_fertility=int(low.sum()),low_and_growing=int((low&t.total_change.gt(0)).sum()),low_and_growing_share=float((low&t.total_change.gt(0)).sum()/low.sum()),population_weighted_growing_share=float(t.loc[low&t.total_change.gt(0),'pop_2023'].sum()/t.loc[low,'pop_2023'].sum())))
    if year==2050:
        t['growth_95_status']=np.select([t['Lower 95 PI'].gt(t.baseline),t['Upper 95 PI'].lt(t.baseline)],['entire_PI_above_baseline','entire_PI_below_baseline'],default='PI_spans_baseline')
        t.loc[t['Lower 95 PI'].isna()|t['Upper 95 PI'].isna(),'growth_95_status']='PI_unavailable'
        save(t.reset_index(),'country_outlook_2050')
save(pd.DataFrame(classifications),'threshold_horizon_sensitivity')
# PI checks are marginal by location. Never sum marginal PI endpoints across countries.
pic=p.loc[p.index.get_level_values('LocID').isin(cm.index)].dropna(subset=['Lower 95 PI','Lower 80 PI','Median PI','Upper 80 PI','Upper 95 PI'])
check('prediction_intervals_nested',((pic['Lower 95 PI']<=pic['Lower 80 PI'])&(pic['Lower 80 PI']<=pic['Median PI'])&(pic['Median PI']<=pic['Upper 80 PI'])&(pic['Upper 80 PI']<=pic['Upper 95 PI'])).all(),len(pic))
# EDA checks needed for comparison with the earlier repository, recomputed from raw data.
eda=[]
for year in [1950,2000,2023,2024,2050,2100]:
    cc=c[c.Time.eq(year)]; ww=world.loc[year]; low=cc.TFR.lt(2.1)
    eda.append(dict(year=year,world_population_billions=float(ww.TPopulation1July/1e6),low_TFR_count=int(low.sum()),TFR_nonmissing=int(cc.TFR.notna().sum()),low_TFR_world_population_share=float(cc.loc[low,'TPopulation1July'].sum()/ww.TPopulation1July),raw_sum_div_world=float(m.loc[m.Time.eq(year),'TPopulation1July'].sum()/ww.TPopulation1July)))
save(pd.DataFrame(eda),'eda_headlines')
peak=world.TPopulation1July.idxmax()
tur=d[d.LocID.eq(792)&d.Time.isin([2050,2100])]
summary={'country_areas':len(cm),'medium_rows':len(m),'country_years_1950_2100':len(c),'supplement_countries':s.LocID.nunique(),'historical_end':2023,'projection_start':2024,'world_peak_july_year':int(peak),'world_peak_billions':float(world.loc[peak,'TPopulation1July']/1e6),'baseline_jan2024_world_billions':float(base.loc[900]/1e6),'turkiye':tur[['Time','baseline','Medium','momentum','mortality','fertility','migration','total_change','Lower 95 PI','Upper 95 PI','fertility_migration_interaction']].to_dict('records'),'threshold_horizon_sensitivity':classifications,'units':'population stocks/components in thousands; percentages in percentage points of Jan 2024 baseline'}
(ROOT/'results/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
# Figures are publication-ready vector PDF plus PNG, explicit units and dates.
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','savefig.facecolor':'white'})
colors={'momentum':'#1F7480','mortality':'#81ACA1','fertility':'#D56E42','migration':'#7764A5'}
def figsave(fig,name):
    fig.savefig(FIG/f'{name}.png',dpi=180,bbox_inches='tight'); fig.savefig(FIG/f'{name}.pdf',bbox_inches='tight'); plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5)); ax.plot(world.index,world.TPopulation1July/1e6,color='#1F7480',lw=2.5)
ax.axvline(2023.5,color='#777777',ls='--',lw=1); ax.axvspan(2024,2100,color='#1F7480',alpha=.06)
ax.scatter([peak],[world.loc[peak,'TPopulation1July']/1e6],color='#D56E42'); ax.annotate(f'{peak}: {world.loc[peak,"TPopulation1July"]/1e6:.2f} billion',(peak,world.loc[peak,'TPopulation1July']/1e6),xytext=(-120,-30),textcoords='offset points')
ax.set(xlabel='Year',ylabel='Population on 1 July (billions)',title='World population: historical estimates and Medium projection',xlim=(1950,2100)); ax.text(1953,9.5,'Estimates'); ax.text(2030,3.3,'Projection'); figsave(fig,'01_world_population')
q=pd.read_csv(TAB/'country_outlook_2050.csv'); fig,ax=plt.subplots(figsize=(10,6))
for cat,col in [('entire_PI_above_baseline','#1F7480'),('PI_spans_baseline','#7B8790'),('entire_PI_below_baseline','#D56E42')]:
    t=q[q.growth_95_status.eq(cat)]; ax.scatter(t.TFR,t.total_change_pct_base,s=18+np.sqrt(t.pop_2023)/4,c=col,alpha=.65,label=cat.replace('_',' '),edgecolors='white',linewidths=.4)
for name in ['Türkiye','China','Japan','India','Nigeria']:
    t=q[q.Location.eq(name)].iloc[0]; ax.annotate(name,(t.TFR,t.total_change_pct_base),xytext=(5,5),textcoords='offset points',fontsize=10)
ax.axvline(2.1,color='#666666',ls='--'); ax.axhline(0,color='#666666',lw=1); ax.set(xlabel='Total fertility rate in 2023 (births per woman)',ylabel='Medium population change, Jan 2024 to Jan 2050 (%)',title='Low fertility does not imply immediate population decline'); ax.legend(fontsize=8,loc='upper left'); figsave(fig,'02_fertility_growth')
ids=[900,792,156,356,566,392,276,840]; z=d[d.Time.eq(2050)&d.LocID.isin(ids)].set_index('LocID').loc[ids]
fig,ax=plt.subplots(figsize=(11,5.6)); pos=np.zeros(len(z)); neg=pos.copy()
for key in components:
    x=z[key+'_pct_base'].values; left=np.where(x>=0,pos,neg); ax.barh(np.arange(len(z)),x,left=left,label=key.title(),color=colors[key]); pos+=np.maximum(x,0);neg+=np.minimum(x,0)
ax.scatter(z.total_change_pct_base,np.arange(len(z)),c='#17242D',marker='D',s=35,label='Net change',zorder=4); ax.set_yticks(np.arange(len(z)),z.Location); ax.invert_yaxis(); ax.axvline(0,color='#777777',lw=.7); ax.set(xlabel='Contribution as % of population on 1 Jan 2024',title='Scenario decomposition of change to 1 Jan 2050'); ax.legend(ncol=5,loc='upper center',bbox_to_anchor=(.5,-.12),fontsize=9); figsave(fig,'03_decomposition')
z=d[d.LocID.eq(792)&d.Time.le(2100)]; fig,ax=plt.subplots(figsize=(10,5.6))
ax.fill_between(z.Time,z['Lower 95 PI']/1000,z['Upper 95 PI']/1000,color='#1F7480',alpha=.13,label='UN 95% prediction interval')
ax.fill_between(z.Time,z['Lower 80 PI']/1000,z['Upper 80 PI']/1000,color='#1F7480',alpha=.17,label='UN 80% prediction interval')
ax.plot(z.Time,z.Medium/1000,color='#1F7480',lw=2.5,label='Medium'); ax.plot(z.Time,z.Momentum/1000,color='#D56E42',lw=2,label='Momentum scenario'); ax.axhline(base.loc[792]/1000,color='#777777',ls='--',label='Jan 2024 baseline')
ax.set(xlabel='Year (1 January)',ylabel='Population (millions)',title='Türkiye: scenario contrasts and projection uncertainty'); ax.legend(fontsize=9,loc='upper left'); figsave(fig,'04_turkiye_uncertainty')
z=d[d.Time.eq(2050)&d.LocID.isin(cm.index)].copy(); z['absolute_interaction']=z.fertility_migration_interaction_pct_base.abs(); z=z.nlargest(12,'absolute_interaction').sort_values('fertility_migration_interaction_pct_base')
fig,ax=plt.subplots(figsize=(10,6)); ax.barh(z.Location,z.fertility_migration_interaction_pct_base,color='#7764A5'); ax.set(xlabel='Difference in migration contribution (percentage points of Jan 2024 population)',title='Fertility and migration contributions depend on scenario order'); figsave(fig,'05_order_sensitivity')
# Persist all checks and provenance before any prior-code inspection.
(ROOT/'results/validation.json').write_text(json.dumps(checks,indent=2,ensure_ascii=False))
(ROOT/'logs/environment.json').write_text(json.dumps({'python':sys.version,'platform':platform.platform(),'pandas':pd.__version__,'numpy':np.__version__,'matplotlib':matplotlib.__version__},indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
print(f'PASS: {len(checks)} checks. All outputs in {ROOT}')
