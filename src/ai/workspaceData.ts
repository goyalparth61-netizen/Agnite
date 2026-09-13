import type { AnalysisContext, AnalysisResult, Observation } from './thermalEngine';
export interface WatchLocation { id:string; name:string; latitude:number; longitude:number; threshold:number; }
export interface SavedReport { id:string; createdAt:string; label:string; classification:string; risk:number; summary:string; report:AnalysisResult; observations:Observation[]; context:AnalysisContext; }
export function distanceKm(a:{latitude:number;longitude:number},b:{latitude:number;longitude:number}){const rad=Math.PI/180;const dlat=(b.latitude-a.latitude)*rad;const dlon=(b.longitude-a.longitude)*rad;const h=Math.min(1,Math.max(0,Math.sin(dlat/2)**2+Math.cos(a.latitude*rad)*Math.cos(b.latitude*rad)*Math.sin(dlon/2)**2));return 6371*2*Math.atan2(Math.sqrt(h),Math.sqrt(1-h));}
export function sampleObservations():Observation[]{const now=Date.now();return [18,21,19,20,55,88].map((frp,index)=>({id:`DEMO-${index}`,latitude:21.1466,longitude:79.0889,observedAt:new Date(now-(5-index)*86400000).toISOString(),frp,brightness:305+frp*.6,source:'demo'}));}
export function readSaved<T>(key:string,validate:(item:unknown)=>item is T):T[]{try{const data=JSON.parse(localStorage.getItem(key)||'[]');return Array.isArray(data)?data.filter(validate).slice(0,50):[];}catch{return [];}}
export function isWatch(item:unknown):item is WatchLocation{if(!item||typeof item!=='object')return false;const x=item as WatchLocation;return typeof x.id==='string'&&typeof x.name==='string'&&Number.isFinite(x.latitude)&&Math.abs(x.latitude)<=90&&Number.isFinite(x.longitude)&&Math.abs(x.longitude)<=180&&Number.isFinite(x.threshold)&&x.threshold>=0;}
export function isSavedReport(item:unknown):item is SavedReport{
 if(!item||typeof item!=='object')return false;
 const x=item as SavedReport;
 if(typeof x.id!=='string'||typeof x.createdAt!=='string'||!Number.isFinite(Date.parse(x.createdAt))||typeof x.label!=='string'||typeof x.classification!=='string'||typeof x.summary!=='string'||!Number.isFinite(x.risk)||!x.report||typeof x.report!=='object'||!Array.isArray(x.report.evidence)||!Array.isArray(x.observations))return false;
 return x.report.evidence.every(entry=>entry&&typeof entry.label==='string'&&typeof entry.value==='string'&&typeof entry.detail==='string')&&x.observations.every(row=>row&&typeof row.source==='string'&&['demo','manual','imported','firms'].includes(row.source));
}
export function downloadText(name:string,text:string,type='application/json'){const url=URL.createObjectURL(new Blob([text],{type}));const link=document.createElement('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
