import { useEffect,useRef,useState } from 'react';
import type { AnalysisContext, Observation } from '../../ai/thermalEngine';
type Feature={id:string;name:string;kind:string;industrial:boolean;distanceKm:number};
type Weather={source:string;sourceUrl:string;observedAt:string|null;windKph:number;windDirectionDeg:number|null;windGustKph:number|null;temperatureC:number|null};
type Context={features:Feature[];limitations:string;fetchedAt:string;weather?:Weather|null;stale?:boolean;warning?:string};
type Props={selected:Pick<Observation,'latitude'|'longitude'|'source'>|null;onSuggestedContext?:(context:AnalysisContext)=>void};

function suggestedContext(features:Feature[],weather?:Weather|null):AnalysisContext {
 const nearestIndustrial=features.filter(feature=>feature.industrial).sort((a,b)=>a.distanceKm-b.distanceKm)[0];
 const nearbyKinds=features.filter(feature=>feature.distanceKm<=2).map(feature=>feature.kind.toLowerCase());
 const landCover:AnalysisContext['landCover']=nearestIndustrial&&nearestIndustrial.distanceKm<=2?'industrial':nearbyKinds.some(kind=>kind.includes('forest')||kind.includes('wood'))?'forest':nearbyKinds.some(kind=>kind.includes('residential'))?'urban':'unknown';
 return {landCover,industrialDistanceKm:nearestIndustrial?.distanceKm??null,windKph:Number.isFinite(weather?.windKph)?Number(weather?.windKph):null};
}

export default function SiteContext({selected,onSuggestedContext}:Props) {
 const [data,setData]=useState<Context|null>(null);const [status,setStatus]=useState('');const [attempt,setAttempt]=useState(0);
 const callback=useRef(onSuggestedContext);callback.current=onSuggestedContext;
 const latitude=selected?.latitude,longitude=selected?.longitude,source=selected?.source;
 useEffect(()=>{
  setData(null);
  if(latitude===undefined||longitude===undefined){setStatus('Select an India-region location to load mapped and weather context.');return;}
  const controller=new AbortController();
  setStatus(source==='demo'?'Loading live OpenStreetMap and weather context for these simulated coordinates…':'Loading nearby industry, geography and current weather…');
  const timer=setTimeout(()=>{
   fetch(`/api/site-context?latitude=${latitude}&longitude=${longitude}`,{signal:controller.signal})
    .then(async response=>{const result=await response.json();if(!response.ok)throw Error(result.error);return result;})
    .then((result:Context)=>{
     setData(result);
     const suggestion=suggestedContext(result.features,result.weather);
     callback.current?.(suggestion);
     const available=[suggestion.landCover!=='unknown'||suggestion.industrialDistanceKm!==null?'mapped land/industry':'',suggestion.windKph!==null?'live wind':''].filter(Boolean).join(' + ');
     const prefix=source==='demo'?'Thermal observations are simulated; context below is live external evidence. ':'Live context loaded. ';
     setStatus(`${prefix}${available?`${available} available. `:''}Review mapped centres and site boundaries before interpreting thermal activity.`);
    })
    .catch(()=>{if(!controller.signal.aborted)setStatus('Live context providers could not be reached. Retry shortly; thermal analysis can still run, but missing context remains unknown.');});
  },350);
  return()=>{clearTimeout(timer);controller.abort();};
 },[latitude,longitude,source,attempt]);
 return <section className="ws-panel"><div className="ws-panel-head"><h2>Nearby industry & geography</h2><span className="ws-kicker">OPENSTREETMAP · 5 KM + LIVE WEATHER</span></div><p role="status">{status}</p>{data&&<><p>{data.limitations}</p>{data.warning&&<div className="ws-notice">{data.warning}</div>}{data.weather&&<div className="ws-evidence"><article className="ws-evidence-item"><span>Current weather context</span><strong>{data.weather.windKph.toFixed(1)} km/h wind</strong><p>{data.weather.temperatureC===null?'Temperature unavailable':`${data.weather.temperatureC.toFixed(1)} °C`} · {data.weather.windGustKph===null?'gust unavailable':`gust ${data.weather.windGustKph.toFixed(1)} km/h`}</p><a href={data.weather.sourceUrl} target="_blank" rel="noreferrer">Open-Meteo source ↗</a></article></div>}<div className="ws-evidence">{data.features.map(feature=><article className="ws-evidence-item" key={feature.id}><span>{feature.industrial?'Potential industrial heat context':'Geographic context'}</span><strong>{feature.name}</strong><p>{feature.kind} · {feature.distanceKm.toFixed(2)} km to mapped centre</p><a href={`https://www.openstreetmap.org/${feature.id}`} target="_blank" rel="noreferrer">Inspect mapped feature ↗</a></article>)}</div>{!data.features.length&&<p>No matching mapped features were returned inside 5 km. This is different from a provider failure: OpenStreetMap coverage can be incomplete, so industrial and land-cover context remain unknown unless you verify them manually.</p>}<p className="ws-source">© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap contributors</a> · retrieved {new Date(data.fetchedAt).toLocaleString()}. {source==='demo'?'The thermal history is simulated even though external context is live. ':''}Mapped context is evidence, not verified facility containment or operating status; you can override it before analysis.</p></>}<button className="ws-button" disabled={!selected} onClick={()=>setAttempt(value=>value+1)}>Retry context lookup</button></section>;
}
