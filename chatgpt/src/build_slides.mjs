import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
process.env.RUNTIME_NODE_MODULES ||= '/Users/buraksahinkucuk/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const SKILL='/Users/buraksahinkucuk/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
const PY='/Users/buraksahinkucuk/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const D=JSON.parse(await fs.readFile(path.join(ROOT,'slides/chart_data.json'),'utf8'));
const notes=JSON.parse(await fs.readFile(path.join(ROOT,'slides/narration.json'),'utf8'));
const deck=Presentation.create({slideSize:{width:1280,height:720}});
const C={ink:'#172C38',muted:'#526570',bg:'#FAFAF6',teal:'#1F7480',orange:'#D56E42',green:'#81ACA1',purple:'#7764A5',grid:'#DFE5E4'};
const FONT='Arial';
function text(sl,txt,x,y,w,h,size=22,color=C.ink,bold=false){const sh=sl.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});sh.text=txt;sh.text.style={fontSize:size,typeface:FONT,color,bold,verticalAlignment:'top',wrap:'square',insets:0};return sh;}
function rect(sl,x,y,w,h,fill){return sl.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}});}
function base(title,subtitle,index){const s=deck.slides.add();s.background.fill=C.bg;text(s,title,56,42,1170,72,36,C.ink,true);if(subtitle)text(s,subtitle,56,120,1168,48,19,C.muted);rect(s,56,670,1168,1,C.grid);text(s,'UN World Population Prospects 2024. Estimates through 2023. Projections from 2024.',56,683,1090,22,12,C.muted);text(s,String(index),1180,680,40,25,15,C.muted);return s;}
function chart(sl,type,config){
// Excel stores 15 significant digits. Round presentation-only chart coordinates to 8 decimals.
for(const series of config.series||[]){series.smooth=false;for(const key of ['values','xValues']){if(series[key])series[key]=series[key].map(v=>v===null?null:Number(v.toFixed(8)));}}
const c=sl.charts.add(type,{chartFill:C.bg,plotAreaFill:C.bg,chartLine:{fill:'none',width:0},...config});applyPresentationChartFont(c,{fontFamily:FONT});return c;}
const axisStyle={fontSize:16,fill:C.muted}; const grid={fill:C.grid,width:1,style:'solid'};
let s=deck.slides.add();s.background.fill=C.ink;
text(s,'ASA International Data Quest Türkiye 2026',64,62,1100,40,21,'#B5D9D8');
text(s,'Low fertility,\ncontinued growth?',64,185,1100,190,66,'#FFFFFF',true);
text(s,'Population momentum and uncertainty to 2050',68,405,1100,60,31,'#DCE8E7');
text(s,'237 countries and areas\nUN World Population Prospects 2024',68,522,1050,90,23,'#B5D9D8');
text(s,'A scenario analysis with a Türkiye case study',68,646,1100,28,17,'#DCE8E7');
s=base('Low fertility and growth coexist in the Medium projection','Fertility in 2023 and population change from 1 Jan 2024 to 1 Jan 2050',1);
const scatterSeries=[{name:'Countries and areas',xValues:D.scatter.map(x=>x.TFR),values:D.scatter.map(x=>x.total_change_pct_base),marker:{symbol:'circle',size:5,fill:C.teal},line:{fill:'none',width:0},points:D.scatter.map((x,idx)=>({idx,fill:x.TFR<2.1?C.teal:'#9AA6A9'}))}];
chart(s,'scatter',{position:{left:48,top:185,width:820,height:445},series:scatterSeries,scatterOptions:{style:'marker'},hasLegend:false,xAxis:{title:'Births per woman (2023)',min:0,max:7,majorUnit:1,textStyle:axisStyle},yAxis:{title:'Medium population change (%)',min:-50,max:150,majorUnit:50,crossesAt:-50,textStyle:axisStyle,majorGridlines:grid,numberFormatCode:'0'}});
text(s,`${D.grow_count} / ${D.low_count}`,928,205,285,90,62,C.teal,true);text(s,'low-fertility places grow\nin the Medium projection',928,300,285,70,23);
text(s,'58%',928,402,270,70,48,C.ink,true);text(s,'of the low-fertility group’s\n2023 population lives there',928,477,290,75,20,C.muted);
text(s,'2.1 is an approximate threshold.\nOne point = one country or area.',928,583,290,55,17,C.muted);
s=base('Scenario contrasts separate four contributions','Change to 1 Jan 2050, expressed as a percentage of the 1 Jan 2024 population',2);
const names={'Türkiye':'Türkiye','United States of America':'USA'};
chart(s,'bar',{position:{left:50,top:180,width:825,height:400},categories:D.decomp.map(x=>names[x.Location]||x.Location),series:[['momentum',C.teal],['mortality',C.green],['fertility',C.orange],['migration',C.purple]].map(([k,col])=>({name:k[0].toUpperCase()+k.slice(1),values:D.decomp.map(x=>x[k+'_pct_base']),fill:col})),barOptions:{direction:'column',grouping:'stacked',gapWidth:65,overlap:100},hasLegend:true,legend:{position:'bottom',textStyle:{fontSize:16,fill:C.ink}},xAxis:{textStyle:axisStyle,tickLabelPosition:'low'},yAxis:{min:-40,max:60,majorUnit:20,textStyle:axisStyle,majorGridlines:grid,numberFormatCode:'0',title:'Contribution (% of baseline)'}});
text(s,'A fixed scenario sequence',918,185,300,55,24,C.ink,true);
text(s,'Momentum\n+ projected mortality\n+ projected fertility\n+ projected migration',918,254,300,174,22,C.muted);
text(s,'The four stock differences\nadd to Medium change.',918,450,300,70,23,C.teal,true);
text(s,'Replacement means NRR = 1.\nThe fertility rate varies\nby country and year.',918,552,300,78,18,C.muted);
text(s,'Contributions depend on the scenario order. They are conditional model contrasts, not causal policy effects.',56,610,805,45,18,C.muted);
s=base('Türkiye grows to 2050 in Medium, with a wide interval','Population on 1 January, millions. The 2024 revision does not represent current observed population.',3);
const tr=D.turkiye;
chart(s,'scatter',{position:{left:42,top:184,width:850,height:453},series:[{name:'Medium',xValues:tr.map(x=>x.Time),values:tr.map(x=>x.Medium/1000),line:{fill:C.teal,width:3},marker:{symbol:'none'}},{name:'95% upper bound',xValues:tr.map(x=>x.Time),values:tr.map(x=>x['Upper 95 PI']/1000),line:{fill:'#9BAEB0',width:2},marker:{symbol:'none'}},{name:'95% lower bound',xValues:tr.map(x=>x.Time),values:tr.map(x=>x['Lower 95 PI']/1000),line:{fill:'#9BAEB0',width:2},marker:{symbol:'none'}},{name:'2024 baseline',xValues:tr.map(x=>x.Time),values:tr.map(x=>x.baseline/1000),line:{fill:C.orange,width:1.5},marker:{symbol:'none'}}],scatterOptions:{style:'line'},hasLegend:true,legend:{position:'bottom',textStyle:{fontSize:14,fill:C.ink}},xAxis:{min:2020,max:2100,majorUnit:20,title:'Year',textStyle:axisStyle,numberFormatCode:'0'},yAxis:{min:0,max:140,majorUnit:20,title:'Population (millions)',textStyle:axisStyle,majorGridlines:grid,numberFormatCode:'0'}});
const turkey=D.summary.turkiye[0];text(s,(turkey.Medium/1000).toFixed(2)+' million',925,210,300,65,37,C.teal,true);text(s,'Medium population in 2050',925,278,300,55,21,C.muted);
text(s,(turkey['Lower 95 PI']/1000).toFixed(2)+'–'+(turkey['Upper 95 PI']/1000).toFixed(2),925,365,300,60,34,C.ink,true);text(s,'UN 95% prediction interval\nThe baseline is 87.37 million.',925,433,300,85,21,C.muted);
text(s,'Positive momentum can\ncoexist with later decline.',925,558,300,72,22,C.orange,true);
s=base('Most Medium growth cases remain uncertain','Among the 64 low-fertility countries and areas that grow in the Medium projection',4);
chart(s,'bar',{position:{left:48,top:182,width:700,height:275},categories:['Entire 95% interval above baseline','95% interval spans baseline'],series:[{name:'Countries and areas',values:[D.robust_count,D.grow_count-D.robust_count],fill:C.teal,points:[{idx:1,fill:'#9CAAAE'}]}],barOptions:{direction:'bar',grouping:'clustered',gapWidth:70},hasLegend:false,dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:24,fill:C.ink,bold:true},numberFormatCode:'0'},xAxis:{textStyle:{fontSize:18,fill:C.muted}},yAxis:{min:0,max:70,majorUnit:20,textStyle:axisStyle,numberFormatCode:'0',majorGridlines:grid}});
text(s,'Sensitivity checks',806,190,410,45,25,C.ink,true);
text(s,'39 / 81 grow with population ≥1 million\n66 / 130 grow under NRR < 1\n28 / 130 grow by 2100 in the original cohort',806,253,410,170,23,C.muted);
rect(s,56,477,1168,2,C.grid);
text(s,'What the intervals can tell us',56,505,535,40,25,C.ink,true);text(s,'Each interval is marginal for one country.\nThey do not give a joint interval for the count.\nScenario effects depend on the chosen path.',56,559,535,90,20,C.muted);
text(s,'Ethical interpretation',684,505,540,40,25,C.ink,true);text(s,'Disclose model assumptions and uncertainty.\nRespect reproductive choices and migrants.\nCountry counts and population weights differ.',684,559,540,90,20,C.muted);
s=base('Sources and reproducible analysis','Data and methods', '');
const refitems=[['UN DESA, Population Division (2024)','World Population Prospects 2024. Medium, OtherVariants and competition supplement. CC BY 3.0 IGO.'],['UN DESA (2024), Methodology, Table II.4, pp. 55–56','Scenario assumptions and the sequential decomposition of projected population change.'],['UN DESA, Demographic Components of Future Population Growth','Methodological background and reference to Andreev, Kantorová and Bongaarts (2013).'],['American Statistical Association (2022)','Ethical Guidelines for Statistical Practice.'],['Analysis package and acknowledgement','Independent scripts, raw-data hashes and validation results are included. Prior EDA: idiltuzkaya/asa_dataquest.']];
refitems.forEach(([h,b],i)=>{text(s,h,58,185+i*82,1165,28,22,C.ink,true);text(s,b,58,217+i*82,1165,42,18,C.muted);});
text(s,'AI assisted the coding, analysis checks and presentation. Team members should review and disclose their contributions.',58,610,1165,42,18,C.teal);
const sources='Sources: https://population.un.org/wpp/ ; https://www.un.org/development/desa/pd/sites/www.un.org.development.desa.pd/files/files/documents/2024/Jul/undesa_pd_2024_wpp2024_methodology-report_web.pdf ; https://www.amstat.org/your-career/ethical-guidelines-for-statistical-practice . Calculations: results/tables/country_outlook_2050.csv and scenario_decomposition.csv.';
for(let i=0;i<deck.slides.items.length;i++){deck.slides.items[i].speakerNotes.text=notes[i]+'\n\n'+sources;}
await fs.mkdir(path.join(ROOT,'.build'),{recursive:true});await fs.mkdir(path.join(ROOT,'slides/previews'),{recursive:true});
const candidate=path.join(ROOT,'.build/candidate.pptx');await(await PresentationFile.exportPptx(deck)).save(candidate);
for(let i=0;i<deck.slides.items.length;i++){const blob=await deck.export({slide:deck.slides.items[i],format:'png',scale:1.5});await fs.writeFile(path.join(ROOT,`slides/previews/slide-${i+1}.png`),new Uint8Array(await blob.arrayBuffer()));}
// PDF exported with bundled LibreOffice after finalization: artifact PDF exporter lacks standard-fonts in this runtime.
const output=process.env.DECK_OUTPUT||'ASA2026_Demographic_Momentum.pptx';
const result=await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:path.join(ROOT,'slides',output),pythonExecutable:PY,integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],explicitTotalSlideCount:6,requiredNativeChartOwnerSlides:[2,3,4,5],requiredNativeTableOwnerSlides:[],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(ROOT,'.build',output+'.validation.json')});
console.log(JSON.stringify(result));
