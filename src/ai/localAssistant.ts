import type {AnalysisResult, Observation} from './thermalEngine';

/** A data-grounded command assistant; intentionally does not impersonate an LLM. */
export function answerQuestion(question:string, observations:Observation[], report:AnalysisResult|null):string {
  const query=question.toLowerCase();
  const provenance=[...new Set(observations.map(row=>row.source))].join(', ');
  if (/highest|strongest|frp|hotspot|sabse/.test(query) && !/how many|count|kitne/.test(query)) {
    if(!observations.length)return 'No observations loaded yet. Open the NASA feed or import a CSV first.';
    const highest=observations.reduce((best,row)=>row.frp>best.frp?row:best);
    return `The highest FRP in the loaded ${provenance} dataset is ${highest.frp.toFixed(1)} MW at ${highest.latitude.toFixed(4)}, ${highest.longitude.toFixed(4)}, observed ${new Date(highest.observedAt).toUTCString()}. FRP is fire radiative power; it does not establish the cause or severity of a fire.`;
  }
  if(/data|count|how many|loaded|source|kitne/.test(query))return `${observations.length.toLocaleString()} observations are loaded. Source: ${provenance||'none'}. NASA records are satellite detections in an India-region bounding box that also includes neighboring areas. Satellite detections are not a count of confirmed fires or cities. When enabled, auto-refresh checks every ten minutes while this workspace is open and visible.`;
  if(/missing|evidence|need|context|kami/.test(query))return report ? `Evidence for the analyzed site: ${report.statistics.distinctTimes} distinct observation times over ${report.statistics.spanHours.toFixed(1)} hours. ${report.warnings.join(' ')}` : 'Select a site and run analysis. Classification needs repeated observations spanning at least 48 hours, two older baseline passes, supplied land cover and industrial distance. Try the 7-day NASA window. Weather and land-cover context are not fetched automatically.';
  if(/class|explain|analysis|kyu|why/.test(query))return report ? `${report.classification}. ${report.summary} ${report.contributions.slice(0,3).map(item=>`${item.feature} ${item.direction} the leading class (${item.contribution.toFixed(2)} logit contribution).`).join(' ')} The classifier was trained on synthetic examples; its scores are not calibrated confidence.` : 'Run site analysis first. I can then explain the result and the feature contributions from that report.';
  if(/risk|predict|forecast|future/.test(query))return report ? `The analyzed site has a heuristic risk index of ${report.risk.index}/100 (${report.risk.level}). ${report.risk.method} The 24h, 48h and 7d ranges are what-if scenarios, not validated forecasts or probabilities.` : 'Run analysis to calculate the transparent risk index. Future ranges are illustrative what-if scenarios, not operational forecasts.';
  if(/next|action|monitor|watch|kya/.test(query))return 'Check the acquisition time and source first. Select a detection, compare the 7-day site history, and provide verified context before classification. Save a report for review or add the coordinates and your FRP threshold to Monitoring. Monitoring checks only the currently loaded NASA feed while the app is open; it does not send emergency notifications.';
  return 'I can answer from the loaded observations and your latest report. Ask about the highest FRP, data sources, classification, missing evidence, risk, or monitoring. This is a local command assistant; a conversational language model is not connected.';
}
