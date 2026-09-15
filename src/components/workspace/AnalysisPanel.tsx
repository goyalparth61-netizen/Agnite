import { useEffect, useRef } from 'react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { BrainCircuit, Download, Play, Save } from 'lucide-react';
import type {AnalysisContext, AnalysisResult, Observation} from '../../ai/thermalEngine';
import {downloadText} from '../../ai/workspaceData';

interface Props { selected:Observation|null; observations:Observation[]; context:AnalysisContext; setContext:(context:AnalysisContext)=>void; report:AnalysisResult|null; run:()=>void; save:()=>void; demo:()=>void; }

type MappedFeature={industrial:boolean;distanceKm:number;kind:string};
function inferMappedContext(features:MappedFeature[]) {
 const nearestIndustrial=features.filter(feature=>feature.industrial).sort((a,b)=>a.distanceKm-b.distanceKm)[0];
 const nearbyKinds=features.filter(feature=>feature.distanceKm<=2).map(feature=>feature.kind.toLowerCase());
 const landCover:AnalysisContext['landCover']=nearestIndustrial&&nearestIndustrial.distanceKm<=2?'industrial':nearbyKinds.some(kind=>kind.includes('forest')||kind.includes('wood'))?'forest':nearbyKinds.some(kind=>kind.includes('residential'))?'urban':'unknown';
 return {landCover,industrialDistanceKm:nearestIndustrial?.distanceKm??null};
}

export default function AnalysisPanel({selected,observations,context,setContext,report,run,save,demo}:Props){
 const contextRef=useRef(context);contextRef.current=context;
 useEffect(()=>{
  if(!selected) return;
  const controller=new AbortController();
  fetch(`/api/site-context?latitude=${selected.latitude}&longitude=${selected.longitude}`,{signal:controller.signal})
   .then(async response=>{if(!response.ok)throw Error('context unavailable');return response.json();})
   .then(result=>{
    if(controller.signal.aborted||!Array.isArray(result.features))return;
    const suggestion=inferMappedContext(result.features);
    const latest=contextRef.current;
    const next:AnalysisContext={
      ...latest,
      landCover:latest.landCover==='unknown'?suggestion.landCover:latest.landCover,
      industrialDistanceKm:latest.industrialDistanceKm===null?suggestion.industrialDistanceKm:latest.industrialDistanceKm,
    };
    if(next.landCover!==latest.landCover||next.industrialDistanceKm!==latest.industrialDistanceKm)setContext(next);
   }).catch(()=>{});
  return()=>controller.abort();
 },[selected?.id,selected?.latitude,selected?.longitude,selected?.source,setContext]);
 return <>
  <div className="ws-panel ws-analysis-hero"><div><span className="ws-kicker">AGNITE AI / EXPERIMENTAL MODEL</span><h2>Evidence before a conclusion.</h2><p>A trained local classifier combines thermal history and spatial context. Ambiguous cases are withheld instead of forcing a label.</p></div><BrainCircuit size={48}/></div>
  <div className="ws-two-col"><section className="ws-panel"><div className="ws-panel-head"><h2>Site & context</h2><span className="ws-status">{selected?.source||'NO DATA'}</span></div>
   {selected?<p className="ws-coordinate">{Math.abs(selected.latitude).toFixed(4)}° {selected.latitude<0?'S':'N'} · {Math.abs(selected.longitude).toFixed(4)}° {selected.longitude<0?'W':'E'}<br/><small>{observations.length} observations within 5 km · analysis is anchored to the selected acquisition</small></p>:<p>Select an observation in the feed or import your data. A selection can expire when the feed updates.</p>}
   <div className="ws-form">
    <label>Land cover<select value={context.landCover} onChange={e=>setContext({...context,landCover:e.target.value as AnalysisContext['landCover']})}><option value="unknown">Unknown</option><option value="forest">Forest</option><option value="industrial">Industrial</option><option value="urban">Urban</option><option value="other">Other</option></select></label>
    <label>Industrial distance (km)<input type="number" min="0" max="20000" step="any" placeholder="Unknown" value={context.industrialDistanceKm??''} onChange={e=>setContext({...context,industrialDistanceKm:e.target.value===''?null:Number(e.target.value)})}/></label>
    <label>Wind speed (km/h)<input type="number" min="0" max="500" step="any" placeholder="Unknown" value={context.windKph??''} onChange={e=>setContext({...context,windKph:e.target.value===''?null:Number(e.target.value)})}/></label>
   </div><p className="ws-source">AGNITE automatically suggests land cover / nearest industrial distance from mapped OpenStreetMap context when available. Treat it as evidence, not verified facility containment; you can override it. Wind remains user supplied. For demo coordinates, mapped context may be live even though the thermal observations remain simulated.</p>
   <div className="ws-actions"><button className="ws-button primary" disabled={!selected} onClick={run}><Play size={15}/> Run analysis</button><button className="ws-button" onClick={demo}>Load demo scenario</button></div>
  </section><section className="ws-panel"><div className="ws-panel-head"><h2>Analysis result</h2>{report&&<span className="ws-status">{report.status}</span>}</div>
   {report?<><span className="ws-kicker">{report.model.name} / V{report.model.version}</span><h2>{report.classification}</h2><p>{report.summary}</p><div className="ws-metrics"><div className="ws-metric"><span>Current screening index</span><strong>{report.risk.index}<small>/100</small></strong><small>{report.risk.level} · heuristic, not fire probability</small></div><div className="ws-metric"><span>Relative classifier score</span><strong>{report.modelScore===null?'WITHHELD':report.modelScore.toFixed(2)}</strong><small>{report.modelScore===null?'Classifier abstained because evidence / decision-gate requirements were not satisfied':'Relative synthetic-model pattern score; not calibrated confidence'}</small></div></div>{report.modelScore===null&&<div className="ws-notice">The blank score was intentional model abstention, not a calculation failure. Check the warnings below for the exact missing-history, context, supported-range, or decision-threshold reason. The separate 24h / 48h / 7d thermal-recurrence pipeline can still produce its own scores when its trained artifact is available.</div>}<div className="ws-actions"><button className="ws-button" onClick={save}><Save size={15}/> Save report</button><button className="ws-button" onClick={()=>downloadText('agnite-analysis.json',JSON.stringify({exportedAt:new Date().toISOString(),context,observations,report},null,2))}><Download size={15}/> Export JSON</button></div></>:<div className="ws-empty">Your result, supporting evidence and model contributions will appear here after analysis.</div>}
  </section></div>
  {report&&<>
   <section className="ws-panel"><div className="ws-panel-head"><h2>Observation evidence</h2><span className="ws-kicker">{report.statistics.included} INCLUDED / {report.statistics.excluded} EXCLUDED</span></div><div className="ws-evidence">{report.evidence.map(item=><article className="ws-evidence-item" key={item.label}><span>{item.label}</span><strong>{item.value}</strong><p>{item.detail}</p></article>)}</div></section>
   <div className="ws-two-col"><section className="ws-panel"><h2>Thermal history</h2><p>Mean FRP per supplied observation time, compared with the median of passes older than 24 hours.</p><div className="ws-chart" role="img" aria-label={`FRP history at ${report.history.length} observation times. Latest ${report.statistics.currentFrp} megawatts.`}><ResponsiveContainer width="100%" height="100%"><AreaChart data={report.history}><CartesianGrid stroke="#303943" vertical={false}/><XAxis dataKey="observedAt" tickFormatter={date=>new Date(date).toLocaleDateString(undefined,{day:'numeric',month:'short'})} stroke="#919ca9" minTickGap={28} tick={{fontSize:10}}/><YAxis stroke="#919ca9" tick={{fontSize:10}} width={36}/><Tooltip labelFormatter={date=>new Date(String(date)).toLocaleString()} contentStyle={{background:'#171d24',borderColor:'#465463'}}/><Area name="FRP (MW)" type="linear" dataKey="frp" stroke="#e6b477" fill="#e6b477" fillOpacity={.13} isAnimationActive={false}/><Area name="Baseline (MW)" type="linear" dataKey="baseline" stroke="#92b9df" fill="none" strokeDasharray="4 4" connectNulls isAnimationActive={false}/></AreaChart></ResponsiveContainer></div><details><summary>View accessible history table</summary><div className="ws-table-wrap"><table className="ws-table"><thead><tr><th>Observed (UTC)</th><th>FRP MW</th><th>Baseline MW</th></tr></thead><tbody>{report.history.map(row=><tr key={row.observedAt}><td>{row.observedAt}</td><td>{row.frp}</td><td>{row.baseline??'—'}</td></tr>)}</tbody></table></div></details></section>
   <section className="ws-panel"><h2>Why this result?</h2><p>Feature contributions compare the leading synthetic class with the runner-up. They are model effects, not causal proof.</p>{report.contributions.length?<div className="ws-score-list">{report.contributions.map(item=><div className="ws-score" key={item.feature}><div><span>{item.feature}</span><strong>{item.contribution>0?'+':''}{item.contribution.toFixed(2)}</strong></div><small>{item.direction} leading class</small><div className="ws-score-track"><i style={{width:`${Math.min(100,Math.abs(item.contribution)*20)}%`,background:item.direction==='supports'?'var(--amber)':'var(--ice)'}}/></div></div>)}</div>:<p>Class contribution details are withheld when the classifier abstains. This prevents an ambiguous synthetic-class score from being presented as a reliable cause label.</p>}<details><summary>Risk index method</summary><p>{report.risk.method}</p></details></section></div>
   <section className="ws-panel"><div className="ws-panel-head"><h2>What-if risk scenarios</h2><span className="ws-status warning">NOT A FORECAST</span></div><div className="ws-scenarios">{report.scenarios.map(item=><article className="ws-scenario" key={item.horizon}><span className="ws-kicker">{item.horizon}</span><h3>{item.low} – {item.high}<small> /100</small></h3><p>{item.assumption}</p></article>)}</div><p className="ws-source">Scenario ranges are illustrative changes around the current index, not confidence intervals or probabilities.</p></section>
   <section className="ws-panel"><h2>Model limits & data quality</h2><ul className="ws-warning-list">{report.warnings.map((warning,index)=><li key={index}>{warning}</li>)}</ul><p className="ws-source">Training: {report.model.trainingSource}. Selective synthetic validation precision: {report.model.selectiveValidationPrecision===null?'unavailable':`${(report.model.selectiveValidationPrecision*100).toFixed(1)}%`} at {(report.model.selectiveValidationCoverage*100).toFixed(1)}% coverage. This is not a real-world accuracy claim.</p></section>
  </>}
 </>;
}
