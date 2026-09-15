import type { Intelligence } from './intelligence';

type ConversationTurn={role:'user'|'assistant';content:string};

function generalDomainAnswer(question:string):string|null{
  const q=question.toLowerCase();
  if(/\bfrp\b|fire radiative power/.test(q)) return 'General explanation: FRP means Fire Radiative Power. It is a satellite-derived estimate of the rate at which radiant energy is being emitted by a thermal source, usually reported in MW. Higher FRP can indicate stronger thermal activity, but FRP alone does not prove that the source is a fire or identify its cause.';
  if(/viirs|modis/.test(q)) return 'General explanation: VIIRS and MODIS are satellite sensors used for Earth observation. NASA FIRMS distributes thermal anomaly / active-fire detections derived from these sensors. VIIRS generally provides finer spatial detail than MODIS, while both depend on satellite overpass timing, clouds, viewing geometry and detection thresholds.';
  if(/nasa firms|\bfirms\b/.test(q)) return 'General explanation: NASA FIRMS is the Fire Information for Resource Management System. It distributes near-real-time satellite thermal anomaly and active-fire products. A FIRMS hotspot is a satellite detection, not automatically a verified incident or confirmed industrial fire.';
  if(/persistent.*heat|industrial heat/.test(q)) return 'General explanation: Persistent industrial heat is thermal activity that repeatedly appears around the same industrial location and may be associated with routine high-temperature processes. AGNITE compares recurrence, baseline behaviour, current FRP deviation and supplied spatial context so repeated normal heat is not automatically treated as an abnormal fire.';
  if(/industrial fire.*forest|forest.*industrial|natural fire/.test(q)) return 'General explanation: AGNITE separates possible industrial fire, persistent industrial heat, forest/natural fire and other thermal anomaly by combining thermal strength, change from historical baseline, recurrence, land-cover context and industrial proximity. These are experimental analytical labels until verified by independent evidence.';
  if(/how.*predict|prediction model|future risk|risk estimate/.test(q)) return 'General explanation: AGNITE has two future-window modes. With the trained recurrence artifact, 24h/48h/7d scores estimate the tendency for another FIRMS thermal detection in the same spatial cell. If that artifact is unavailable, AGNITE falls back to a transparent heuristic simulation. Neither mode is a calibrated probability of a confirmed fire or an exact future fire time.';
  if(/what is agnite|how.*agnite work|agnite ai/.test(q)) return 'General explanation: AGNITE combines NASA FIRMS thermal observations, spatial context, historical behaviour, experimental classification, persistent-heat analysis, recurrence/risk windows and an evidence-grounded AI assistant. The AI explains the selected hotspot and can also answer general thermal-intelligence questions.';
  if(/brightness|temperature/.test(q)) return 'General explanation: Satellite brightness temperature is a remotely sensed radiance-derived temperature for the observed pixel/band. It is not the same as a thermometer reading at ground level and should not be presented as exact surface temperature without appropriate interpretation.';
  if(/safe|safety|precaution|prevent/.test(q)&&!/this|here|selected|location|site/.test(q)) return 'General guidance: verify the source, avoid approaching suspected fire or hazardous industrial areas, monitor official local alerts, maintain safe evacuation access, and contact responsible emergency or site authorities when there is a confirmed threat. Satellite detections are decision-support evidence, not a replacement for field verification.';
  return null;
}

export function localAnswer(question: string, data: Intelligence): string {
  const generic=generalDomainAnswer(question);
  if(!data.selected) return generic??'Select a hotspot for location-specific analysis. I can still explain NASA FIRMS, FRP, VIIRS/MODIS, persistent industrial heat, AGNITE risk methodology and general safety concepts.';
  const {history:h,report,predictions,selected:s}=data;
  const q=question.toLowerCase();
  const header=`${s.latitude.toFixed(4)}, ${s.longitude.toFixed(4)} | ${s.observedAt} | source: ${s.source==='demo'?'SIMULATED DATA':s.source==='firms'?'NASA FIRMS':s.source==='imported'?'IMPORTED':'LOCAL / MANUAL'}`;
  const baselineText=h.baselineFrp===null?'not established because no earlier pass is available in the loaded history':`${h.baselineFrp.toFixed(1)} MW`;
  const deviationText=h.anomalyPercent===null?'not calculated because a baseline is not established':`${h.anomalyPercent.toFixed(1)}%`;
  const persistenceText=h.persistenceScore===null?'not calculated yet; detections on at least two calendar days are needed':`${h.persistenceScore} /100`;
  const recurrenceText=h.recurrencePerDay===null?'not calculated yet; at least 24 hours of observed span are needed':`${h.recurrencePerDay.toFixed(2)} repeated passes/day`;
  const history=`${h.historicalDetections} historical thermal detections; ${h.distinctPasses} distinct passes including current. Earliest: ${h.earliest??'no earlier pass loaded'}. Latest: ${h.latest??'no pass loaded'}. Peak FRP: ${h.peakFrp?.toFixed(1)??'not available'} MW; average: ${h.averageFrp?.toFixed(1)??'not available'} MW. Baseline: ${baselineText}; selected signal: ${s.frp} MW; deviation: ${deviationText}. Trend: ${h.trend}. Persistence: ${persistenceText}. Recurrence: ${recurrenceText}. Saved reports: ${data.savedReports.length}.`;
  const classification=`Classification: ${report?.classification??'not available yet — Run site analysis first'}. Current screening risk: ${report?.risk.index??'not available yet'}/100. ${report?.evidence.map(e=>`${e.label}: ${e.value} — ${e.detail}`).join('\n')??'Analysis evidence is not available until site analysis can run.'} Classification is experimental, not a confirmed cause.`;
  const prediction=predictions.length?predictions.map(p=>`${p.window}: ${p.riskScore}/100 (${p.level}); evidence confidence ${p.confidence}.\nWHY THIS SCORE?\n${p.contributingFactors.map(f=>`${f.points>=0?'+':''}${f.points} ${f.label}`).join('; ')||'No listed factors'}.\nMissing evidence: ${p.missingEvidence.join('; ')||'No listed input gaps; field validation is still unavailable'}.\n${p.explanation}`).join('\n\n'):'Future risk windows are not available for this selection.';
  const predictionDisclaimer=data.predictionMode==='real-recurrence-model'?'Thermal-recurrence model score — not a confirmed-fire probability or exact event-time prediction.':'Risk estimate / simulation — not a confirmed future fire prediction.';
  let answer: string;
  if(/why.*(?:unavailable|missing)|baseline.*(?:unavailable|missing)|no baseline|not available/.test(q)) answer=`The current signal is real loaded evidence, but some derived fields need history or context. Baseline: ${baselineText}. Deviation: ${deviationText}. Persistence: ${persistenceText}. Recurrence: ${recurrenceText}. For live NASA data, switch the observation window to 7 days or try another sensor to look for more prior passes. Missing map or wind context should stay unknown rather than being guessed.`;
  else if(/missing|confidence|uncertain/.test(q)) answer=`Missing evidence: ${predictions[0]?.missingEvidence.join('; ')||'No listed input gaps'}. Verified incident labels, ground verification, complete historical coverage, weather forecasts and validated predictive accuracy may be unavailable. Brightness: ${s.brightness===undefined?'not reported by the selected source':`${s.brightness} K (satellite brightness temperature, not a ground thermometer reading)`}.`;
  else if(/future|predict|next|24|48|7.day|when.*fire|happen next/.test(q)) answer=`${prediction}\n\nAGNITE cannot determine an exact future fire time from this evidence. ${predictionDisclaimer}`;
  else if(/prevent|precaution|safety|action|mitigat/.test(q)) answer=`Current screening risk: ${report?.risk.index??'not available until analysis runs'}/100; trend: ${h.trend}. Verify the satellite acquisition and local conditions, compare repeated passes with the historical baseline when enough history exists, inspect available industrial/land-cover context, and escalate to responsible local authorities or site authorities when field evidence indicates a real emergency. ${h.trend==='rising'?'The rising FRP trend supports closer monitoring and field verification.':'Continue monitoring for meaningful change.'}`;
  else if(/baseline|history|historical|past|previous|repeat|persist|trend/.test(q)) answer=`${history}\n${/industrial/.test(q)?classification:''}\n${data.savedReports.slice(0,5).map(r=>`Saved snapshot ${r.createdAt}: ${r.classification}. ${r.summary}`).join('\n')}`;
  else if(/why.*risk|risk.*high/.test(q)) answer=`${prediction}\n\n${predictionDisclaimer}`;
  else if(/simple|simply/.test(q)) answer='The satellite detected heat at this location. Heat can come from industry, vegetation or other sources, so the detection alone does not confirm a fire. '+(report?.summary??'More evidence is needed to classify this site reliably.');
  else if(/classif|why|risk/.test(q)) answer=classification;
  else if(/source|nasa/.test(q)) answer=`Source labels in location history: ${[...new Set(h.rows.map(r=>r.source))].join(', ')}. NASA FIRMS means satellite-derived thermal detections; imported/manual provenance is unverified; demo means SIMULATED DATA.`;
  else if(generic) return `${generic}\n\nSelected hotspot context: ${header}. Current selected FRP: ${s.frp.toFixed(1)} MW.`;
  else answer=`${history}\n\n${classification}\n\nEstimated future windows: ${predictions.map(p=>`${p.window} ${p.riskScore}/100 (${p.level})`).join(', ')||'not available'}. ${predictionDisclaimer} Ask me about history, classification, risk factors, prediction, FRP, FIRMS, persistent heat or precautions.`;
  return `${header}\n\n${answer}\n\n${data.limitations}`;
}

export async function askAgnite(question: string, context: Intelligence, conversationOrFetch:ConversationTurn[]|typeof fetch=[], fetchImplArg: typeof fetch = fetch) {
  const conversation=typeof conversationOrFetch==='function'?[]:conversationOrFetch;
  const fetchImpl=typeof conversationOrFetch==='function'?conversationOrFetch:fetchImplArg;
  const fallback=(reason:string)=>({answer:localAnswer(question,context),mode:'local' as const,reason});
  try {
    const safeConversation=conversation.slice(-8).map(item=>({role:item.role,content:item.content.slice(0,1200)}));
    const response=await fetchImpl('/api/agnite/ask',{method:'POST',headers:{'Content-Type':'application/json'},signal:AbortSignal.timeout(30000),body:JSON.stringify({question,conversation:safeConversation,context:{...context,history:{...context.history,rows:context.history.rows.slice(-100),gapsHours:context.history.gapsHours.slice(-100)},savedReports:context.savedReports.slice(0,10)}})});
    if(!response.ok) return fallback('AI service unavailable; answered locally from the selected evidence.');
    const result=await response.json();
    if(result.mode!=='provider'||typeof result.answer!=='string'||!result.answer.trim()) return fallback(typeof result.reason==='string'&&result.reason.trim()?`${result.reason} Answered locally from the selected evidence.`:'External AI is not configured; answered locally from the selected evidence.');
    return {answer:result.answer.slice(0,16000),mode:'provider' as const,reason:''};
  } catch {return fallback('Network or provider timeout; answered locally from the selected evidence.');}
}
