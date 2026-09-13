import type { Intelligence } from './intelligence';

export function localAnswer(question: string, data: Intelligence): string {
  if(!data.selected) return 'Select a hotspot first. Location-specific evidence is unavailable.';
  const {history:h,report,predictions,selected:s}=data;
  const q=question.toLowerCase();
  const header=`${s.latitude.toFixed(4)}, ${s.longitude.toFixed(4)} | ${s.observedAt} | source: ${s.source==='demo'?'SIMULATED DATA':s.source==='firms'?'NASA FIRMS':s.source==='imported'?'IMPORTED':'LOCAL / MANUAL'}`;
  const history=`${h.historicalDetections} historical thermal detections; ${h.distinctPasses} distinct passes including current. Earliest: ${h.earliest??'unavailable'}. Latest: ${h.latest??'unavailable'}. Peak FRP: ${h.peakFrp?.toFixed(1)??'unavailable'} MW; average: ${h.averageFrp?.toFixed(1)??'unavailable'} MW. Baseline: ${h.baselineFrp?.toFixed(1)??'unavailable'} MW; selected signal: ${s.frp} MW; deviation: ${h.anomalyPercent?.toFixed(1)??'unavailable'}%. Trend: ${h.trend}. Persistence: ${h.persistenceScore??'unavailable'} /100. Recurrence: ${h.recurrencePerDay?.toFixed(2)??'unavailable'} repeated passes/day. Gaps: ${h.gapsHours.slice(-20).map(n=>n.toFixed(1)).join(', ')||'unavailable'} hours (latest 20). Saved reports: ${data.savedReports.length}.`;
  const classification=`Classification: ${report?.classification??'unavailable — Run site analysis first'}. Current risk: ${report?.risk.index??'unavailable'}/100. ${report?.evidence.map(e=>`${e.label}: ${e.value} — ${e.detail}`).join('\n')??'Analysis evidence unavailable.'} Classification is experimental, not a confirmed cause.`;
  const prediction=predictions.map(p=>`${p.window}: ${p.riskScore}/100 ${p.level}, evidence confidence ${p.confidence}\nWHY THIS SCORE?\n${p.contributingFactors.map(f=>`${f.points>=0?'+':''}${f.points}: ${f.label}`).join('\n')}\nMissing evidence: ${p.missingEvidence.join('; ')||'No listed gaps; field validation still unavailable'}.\n${p.explanation}`).join('\n\n');
  let answer: string;
  if(/missing|confidence|uncertain/.test(q)) answer=`Missing evidence: ${predictions[0]?.missingEvidence.join('; ')||'No listed input gaps'}. Verified incident labels, ground verification, weather forecasts and validated prediction accuracy are unavailable. Brightness: ${s.brightness===undefined?'unavailable':`${s.brightness} K (satellite brightness, not ground temperature)`}.`;
  else if(/future|predict|next|24|48|7.day|happen next/.test(q)) answer=prediction;
  else if(/prevent|precaution|safety|action|mitigat/.test(q)) answer=`Current risk: ${report?.risk.index??'unavailable'}/100; trend ${h.trend}. Verify the acquisition and local conditions. Compare repeated passes with the baseline; check supplied land cover and industrial context. ${h.trend==='rising'?'Rising FRP warrants closer monitoring and field verification.':'Continue monitoring for changes.'} Follow responsible local authorities for verified emergency conditions.`;
  else if(/baseline|history|historical|past|previous|repeat|persist|trend/.test(q)) answer=`${history}\n${/industrial/.test(q)?classification:''}\n${data.savedReports.slice(0,5).map(r=>`Saved snapshot ${r.createdAt}: ${r.classification}. ${r.summary}`).join('\n')}`;
  else if(/why.*risk|risk.*high/.test(q)) answer=prediction;
  else if(/simple|simply/.test(q)) answer='The satellite detected heat at this location. Heat can come from industry, vegetation or other sources; it does not confirm a fire. '+(report?.summary??'More evidence is needed to classify this location.');
  else if(/classif|why|risk/.test(q)) answer=classification;
  else if(/source|nasa/.test(q)) answer=`Source labels in location history: ${[...new Set(h.rows.map(r=>r.source))].join(', ')}. Imported/manual provenance is unverified; demo is SIMULATED DATA.`;
  else answer=`${history}\n\n${classification}\n\n${/technical|complete/.test(q)?prediction:`Selected FRP is the radiative power of this thermal detection. It does not by itself prove a fire or its cause. Estimated risk: ${predictions.map(p=>`${p.window} ${p.riskScore}/100 (${p.level})`).join(', ')}; unvalidated simulation.`}`;
  return `${header}\n\n${answer}\n\n${data.limitations}`;
}

export async function askAgnite(question: string, context: Intelligence, fetchImpl: typeof fetch = fetch) {
  const fallback=(reason:string)=>({answer:localAnswer(question,context),mode:'local' as const,reason});
  try {
    const response=await fetchImpl('/api/agnite/ask',{method:'POST',headers:{'Content-Type':'application/json'},signal:AbortSignal.timeout(25000),body:JSON.stringify({question,context:{...context,history:{...context.history,rows:context.history.rows.slice(-100),gapsHours:context.history.gapsHours.slice(-100)},savedReports:context.savedReports.slice(0,10)}})});
    if(!response.ok) return fallback('AI service unavailable; answered locally.');
    const result=await response.json();
    if(result.mode!=='provider'||typeof result.answer!=='string'||!result.answer.trim()) return fallback('External AI unavailable or unconfigured; answered locally.');
    return {answer:result.answer.slice(0,16000),mode:'provider' as const,reason:''};
  } catch {return fallback('Network or provider timeout; answered locally.');}
}
