import type { AnalysisContext, AnalysisResult, Observation } from './thermalEngine.ts';
import type { SavedReport } from './workspaceData.ts';
import { recurrenceModelStatus, recurrencePredictions } from './recurrenceModel.ts';

const DAY = 86400000;
const mean = (v: number[]) => v.length ? v.reduce((a, b) => a + b, 0) / v.length : null;
const bounded = (n: number) => Math.max(0, Math.min(100, Number.isFinite(n) ? n : 0));
export const sourceLabel = (source: Observation['source']) => ({ firms: 'NASA DATA', imported: 'IMPORTED DATA', manual: 'MANUAL DATA', demo: 'SIMULATED DATA' })[source];
function distance(a: Observation, b: Observation) {
  const r = Math.PI / 180;
  const h = Math.sin((a.latitude-b.latitude)*r/2)**2 + Math.cos(a.latitude*r)*Math.cos(b.latitude*r)*Math.sin((a.longitude-b.longitude)*r/2)**2;
  return 12742 * Math.asin(Math.sqrt(Math.min(1, Math.max(0,h))));
}
export function summarizeLocation(selected: Observation | null, observations: Observation[], radiusKm = 5) {
  const seen = new Set<string>();
  const rows = selected ? [selected, ...observations].filter(row => {
    const key = `${row.source}:${row.latitude}:${row.longitude}:${Date.parse(row.observedAt)}`;
    if (!Number.isFinite(row.frp) || row.frp < 0 || !Number.isFinite(Date.parse(row.observedAt)) || Date.parse(row.observedAt)>Date.parse(selected.observedAt) || distance(row,selected)>radiusKm || !Number.isFinite(distance(row,selected)) || (row.source==='demo') !== (selected.source==='demo') || seen.has(key)) return false;
    seen.add(key); return true;
  }).sort((a,b)=>Date.parse(a.observedAt)-Date.parse(b.observedAt)) : [];
  const historical = rows.filter(row=>Date.parse(row.observedAt)<Date.parse(selected!.observedAt));
  const grouped = new Map<number,{sum:number;count:number}>();
  for(const row of rows) {const time=Date.parse(row.observedAt);const pass=grouped.get(time)??{sum:0,count:0};pass.sum+=row.frp;pass.count++;grouped.set(time,pass);}
  const times = [...grouped.keys()];
  const passes = [...grouped].map(([time,p])=>({time,frp:p.sum/p.count}));
  const gapsHours = times.slice(1).map((t,i)=>(t-times[i])/3600000);
  const spanDays = times.length ? (times[times.length-1]-times[0])/DAY : 0;
  const days = new Set(times.map(t=>Math.floor(t/DAY))).size;
  const baseline = mean(passes.filter(p=>p.time<Date.parse(selected!.observedAt)).map(p=>p.frp));
  const recent = passes.slice(-5);
  const change = recent.length>1 ? recent[recent.length-1].frp-recent[0].frp : null;
  const trend = change===null ? 'unknown' : Math.abs(change)<=Math.max(1,recent[0].frp*.1) ? 'stable' : change>0 ? 'rising' : 'falling';
  return {radiusKm, rows, historicalDetections:historical.length, totalDetections:rows.length,
    earliest:rows[0]?.observedAt??null, latest:rows[rows.length-1]?.observedAt??null,
    peakFrp:rows.length?rows.reduce((peak,r)=>Math.max(peak,r.frp),0):null, averageFrp:mean(rows.map(r=>r.frp)),
    distinctPasses:times.length, repeatedDetections:Math.max(0,times.length-1), gapsHours, spanDays,
    recurrencePerDay:spanDays>=1?(times.length-1)/spanDays:null,
    persistenceScore:days>=2?Math.round(100*days/(Math.floor(times[times.length-1]/DAY)-Math.floor(times[0]/DAY)+1)):null,
    baselineFrp:baseline, currentFrp:selected?.frp??null,
    anomalyPercent:baseline!==null&&baseline>0&&selected?100*(selected.frp-baseline)/baseline:null, trend};
}
export type LocationHistory = ReturnType<typeof summarizeLocation>;
export type WeatherAssessment = {points:number;factors:{label:string;points:number}[];summary:string;missing:string[]};
export function assessWeather(context: AnalysisContext):WeatherAssessment {
  const w=context.weather;
  if(!w) return {points:0,factors:[],summary:'Weather data unavailable; no weather adjustment applied.',missing:['Weather unavailable']};
  const factors:{label:string;points:number}[]=[];
  const wind=w.windKph??context.windKph;
  if(wind!==null) factors.push({label:`Wind ${wind.toFixed(1)} km/h`,points:Math.min(6,wind/8)});
  if(w.windGustKph!==null) factors.push({label:`Wind gusts ${w.windGustKph.toFixed(1)} km/h`,points:Math.min(3,w.windGustKph/20)});
  if(w.humidityPercent!==null) factors.push({label:`Humidity ${w.humidityPercent.toFixed(0)}%`,points:w.humidityPercent<20?5:w.humidityPercent<35?3:w.humidityPercent>75?-2:0});
  if(w.temperatureC!==null&&w.humidityPercent!==null) factors.push({label:`Temperature ${w.temperatureC.toFixed(1)} °C`,points:w.temperatureC>=38&&w.humidityPercent<35?2:w.temperatureC>=32&&w.humidityPercent<35?1:0});
  const rain=w.rainMm??w.precipitationMm;
  if(rain!==null) factors.push({label:`Current rain ${rain.toFixed(1)} mm`,points:rain>=7.5?-5:rain>=2.5?-3:rain>0?-1:0});
  const raw=factors.reduce((sum,factor)=>sum+factor.points,0);
  const points=Math.max(-6,Math.min(15,raw));
  const dry=w.humidityPercent!==null&&w.humidityPercent<35;
  const windy=wind!==null&&wind>=25;
  const wet=rain!==null&&rain>=2.5;
  const summary=wet?'Rainfall may reduce immediate vegetation fire-spread concern, but it does not identify the thermal source.':dry&&windy?'Dry air and stronger winds may increase spread concern if the thermal event is an active fire.':dry?'Low humidity adds dry-condition context to this thermal signal.':windy?'Stronger winds may increase spread concern if an active fire is present.':'Weather currently adds limited spread-risk context.';
  const missing=[w.humidityPercent===null?'Humidity unavailable':null,wind===null?'Wind unavailable':null,rain===null?'Rainfall unavailable':null,w.temperatureC===null?'Temperature unavailable':null].filter((value):value is string=>Boolean(value));
  return {points:Math.round(points*10)/10,factors:factors.map(f=>({...f,points:Math.round(f.points*10)/10})),summary,missing};
}


/** Transparent fallback used until a real historical recurrence artifact is trained. */
export function estimateRisk(history: LocationHistory, context: AnalysisContext, report: AnalysisResult | null) {
  if(history.currentFrp===null) return [];
  const weather=assessWeather(context);
  const factors = [
    {label:'Current FRP (log-scaled)',points:Math.min(30,Math.log1p(history.currentFrp)*6)},
    {label:'Deviation from historical baseline',points:history.anomalyPercent===null?0:Math.max(-15,Math.min(20,history.anomalyPercent/10))},
    {label:`Recent trend: ${history.trend}`,points:history.trend==='rising'?10:history.trend==='falling'?-10:0},
    {label:'Repeated passes / recurrence',points:Math.min(10,history.repeatedDetections*2)+(history.recurrencePerDay===null?0:Math.min(5,history.recurrencePerDay*2))},
    {label:'Observed day persistence',points:(history.persistenceScore??0)*.05},
    {label:'Current classification risk index',points:(report?.risk.index??0)*.15},
    {label:'Supplied industrial proximity (< 2 km)',points:context.industrialDistanceKm!==null&&context.industrialDistanceKm<2?5:0},
    {label:`Supplied land cover: ${context.landCover}`,points:context.landCover==='forest'?5:context.landCover==='industrial'?3:0},
    ...weather.factors.map(f=>({label:`Weather context: ${f.label}`,points:f.points})),
  ];
  const missing = [history.distinctPasses<3||history.spanDays<7?'Limited historical depth':null,history.baselineFrp===null?'Historical baseline unavailable':null,context.landCover==='unknown'?'Land cover unavailable':null,context.industrialDistanceKm===null?'Industrial distance unavailable':null,!report?'Classification analysis unavailable':null,...weather.missing].filter((v):v is string=>!!v);
  return (['24h','48h','7d'] as const).map((window,i)=>{
    const horizonPoints=(history.trend==='rising'?1:history.trend==='falling'?-1:0)*[0,3,7][i];
    const contributingFactors=[...factors,{label:'Assumed trend continuation over horizon',points:horizonPoints}].map(f=>({...f,points:Math.round(f.points*10)/10}));
    const riskScore=Math.round(bounded(contributingFactors.reduce((s,f)=>s+f.points,0)));
    return {window,riskScore,level:riskScore>=80?'CRITICAL':riskScore>=60?'HIGH':riskScore>=30?'MODERATE':'LOW',confidence:missing.length||i===2?'LOW':'MODERATE',contributingFactors,missingEvidence:missing,
      explanation:'RISK ESTIMATE / SIMULATION anchored to the selected acquisition, assuming trend continuation. Sum of displayed heuristic points, clamped to 0–100. Confidence describes evidence coverage, not calibrated accuracy. Not a fire probability, weather forecast or exact event date.'};
  });
}

function estimateWithRecurrenceModel(selected: Observation | null, history: LocationHistory, context: AnalysisContext) {
  const learned = recurrencePredictions(selected, history, context);
  if (!learned?.length) return null;
  return learned.map((prediction) => {
    const riskScore = Math.round(bounded(prediction.score * 100));
    const highPrecisionDecision = prediction.targetMet && prediction.score >= prediction.threshold;
    const missingEvidence = [
      history.distinctPasses < 3 ? 'Limited recent history at this location' : null,
      context.landCover === 'unknown' ? 'Land cover unavailable' : null,
      context.windKph === null ? 'Wind unavailable' : null,
      context.industrialDistanceKm === null ? 'Industrial distance unavailable' : null,
      prediction.targetMet ? null : '99% validation-precision target was not achieved for this horizon',
      highPrecisionDecision ? null : 'Model score is below the conservative high-precision decision threshold',
      'Thermal recurrence is not the same as a verified fire incident',
    ].filter((value): value is string => Boolean(value));
    return {
      window: prediction.window,
      riskScore,
      level: riskScore>=80?'CRITICAL':riskScore>=60?'HIGH':riskScore>=30?'MODERATE':'LOW',
      confidence: highPrecisionDecision ? 'HIGH' : prediction.targetMet ? 'MODERATE' : 'LOW',
      contributingFactors: [
        {label:'NASA FIRMS historical recurrence model score',points:Math.round(prediction.score*1000)/10},
        {label:'Conservative decision threshold',points:Math.round(prediction.threshold*1000)/10},
        {label:`Recent trend: ${history.trend}`,points:history.trend==='rising'?10:history.trend==='falling'?-10:0},
        {label:'Repeated historical passes',points:Math.min(10,history.repeatedDetections)},
      ],
      missingEvidence,
      explanation:`REAL-DATA THERMAL RECURRENCE MODEL v${prediction.modelVersion}. Score estimates the tendency for another FIRMS thermal detection in this spatial cell within ${prediction.window}; it is not a calibrated probability of a confirmed fire. Validation precision at the conservative threshold: ${prediction.achievedPrecision===null?'unavailable':(prediction.achievedPrecision*100).toFixed(1)+'%'}. Target: ${(prediction.targetPrecision*100).toFixed(0)}%.`,
    };
  });
}

export function buildIntelligence(selected: Observation|null, observations: Observation[], context: AnalysisContext, report: AnalysisResult|null, saved: SavedReport[] = []) {
  const relevant = selected ? saved.filter(s=>s.observations?.some(r=>distance(r,selected)<=5&&(r.source==='demo')===(selected.source==='demo'))) : [];
  const history=summarizeLocation(selected,[...observations,...relevant.flatMap(s=>s.observations)]);
  const learnedPredictions = estimateWithRecurrenceModel(selected, history, context);
  const recurrenceModel = recurrenceModelStatus();
  return {
    selected,
    context,
    report,
    history,
    predictions: learnedPredictions ?? estimateRisk(history,context,report),
    predictionMode: learnedPredictions ? 'real-recurrence-model' as const : 'heuristic-simulation' as const,
    recurrenceModel,
    weatherAssessment: assessWeather(context),
    savedReports:relevant.map(s=>({id:s.id,createdAt:s.createdAt,classification:s.classification,summary:s.summary,evidence:s.report.evidence})),
    limitations:`Loaded thermal detections only, not verified incidents. Missing passes and non-detections are unknown. Baseline is mean FRP of prior distinct passes within 5 km; later observations excluded. Simulated and non-simulated history are separated. ${learnedPredictions?'Future windows use a historically trained thermal-recurrence model; recurrence is not a confirmed-fire forecast.':'Future windows use a transparent heuristic simulation until a real historical recurrence artifact is trained.'}`
  };
}
export type Intelligence = ReturnType<typeof buildIntelligence>;
