import { useEffect,useRef,useState } from 'react';
import type { AnalysisContext, Observation } from '../../ai/thermalEngine';
type Feature={id:string;name:string;kind:string;industrial:boolean;distanceKm:number};
type Context={features:Feature[];limitations:string;fetchedAt:string};
type Props={selected:Pick<Observation,'latitude'|'longitude'|'source'>|null;onSuggestedContext?:(context:AnalysisContext)=>void};

function suggestedContext(features:Feature[]):AnalysisContext {
 const nearestIndustrial=features.filter(feature=>feature.industrial).sort((a,b)=>a.distanceKm-b.distanceKm)[0];
 const nearbyKinds=features.filter(feature=>feature.distanceKm<=2).map(feature=>feature.kind.toLowerCase());
 const landCover:AnalysisContext['landCover']=nearestIndustrial&&nearestIndustrial.distanceKm<=2?'industrial':nearbyKinds.some(kind=>kind.includes('forest')||kind.includes('wood'))?'forest':nearbyKinds.some(kind=>kind.includes('residential'))?'urban':'unknown';
 return {landCover,industrialDistanceKm:nearestIndustrial?.distanceKm??null,windKph:null};
}

export default function SiteContext({selected,onSuggestedContext}:Props) {
 const [data,setData]=useState<Context|null>(null);const [status,setStatus]=useState('');const [attempt,setAttempt]=useState(0);
 const callback=useRef(onSuggestedContext);callback.current=onSuggestedContext;
 const latitude=selected?.latitude,longitude=selected?.longitude,source=selected?.source;
 useEffect(()=>{setData(null);if(latitude===undefined||longitude===undefined||source==='demo'){setStatus('Select a non-demo India-region location to load mapped context.');return;}const controller=new AbortController();setStatus('Loading nearby industry and geographic features…');const timer=setTimeout(()=>{fetch(`/api/site-context?latitude=${latitude}&longitude=${longitude}`,{signal:controller.signal}).then(async response=>{const result=await response.json();if(!response.ok)throw Error(result.error);return result;}).then((result:Context)=>{setData(result);const suggestion=suggestedContext(result.features);callback.current?.(suggestion);setStatus(`Mapped context loaded${suggestion.landCover!=='unknown'||suggestion.industrialDistanceKm!==null?' and suggested as analysis context':''}. Review site boundaries before interpreting thermal activity.`);}).catch(()=>{if(!controller.signal.aborted)setStatus('Nearby map context could not load. Retry or enter verified context below.');});},500);return()=>{clearTimeout(timer);controller.abort();};},[latitude,longitude,source,attempt]);
 return <section className="ws-panel"><div className="ws-panel-head"><h2>Nearby industry & geography</h2><span className="ws-kicker">OPENSTREETMAP · 5 KM SEARCH</span></div><p role="status">{status}</p>{data&&<><p>{data.limitations}</p><div className="ws-evidence">{data.features.map(feature=><article className="ws-evidence-item" key={feature.id}><span>{feature.industrial?'Potential industrial heat context':'Geographic context'}</span><strong>{feature.name}</strong><p>{feature.kind} · {feature.distanceKm.toFixed(2)} km to mapped centre</p><a href={`https://www.openstreetmap.org/${feature.id}`} target="_blank" rel="noreferrer">Inspect mapped feature ↗</a></article>)}</div>{!data.features.length&&<p>No matching features were returned. Industrial and land-cover context remain unknown.</p>}<p className="ws-source">© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap contributors</a> · retrieved {new Date(data.fetchedAt).toLocaleString()}. Mapped context is an automatic suggestion, not verified facility containment or operating status; you can override it before analysis.</p></>}<button className="ws-button" disabled={!selected||source==='demo'} onClick={()=>setAttempt(value=>value+1)}>Retry context lookup</button></section>;
}
