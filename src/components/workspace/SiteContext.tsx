import { useEffect,useRef,useState } from 'react';
import type { AnalysisContext, Observation } from '../../ai/thermalEngine';
type Feature={id:string;name:string;kind:string;industrial:boolean;distanceKm:number};
type Weather={source:string;sourceUrl:string;observedAt:string|null;temperatureC:number|null;humidityPercent:number|null;precipitationMm:number|null;rainMm:number|null;windKph:number|null;windDirectionDeg:number|null;windDirectionLabel:string|null;windGustKph:number|null;forecast24h?:{minTemperatureC:number|null;maxTemperatureC:number|null;minHumidityPercent:number|null;maxWindKph:number|null;maxWindGustKph:number|null;precipitationTotalMm:number|null;rainTotalMm:number|null}|null};
type Context={features:Feature[];limitations:string;fetchedAt:string;weather?:Weather|null;stale?:boolean;warning?:string};
type Props={selected:Pick<Observation,'latitude'|'longitude'|'source'>|null;onSuggestedContext?:(context:AnalysisContext)=>void};

function suggestedContext(features:Feature[],weather?:Weather|null):AnalysisContext {
 const nearestIndustrial=features.filter(feature=>feature.industrial).sort((a,b)=>a.distanceKm-b.distanceKm)[0];
 const nearbyKinds=features.filter(feature=>feature.distanceKm<=2).map(feature=>feature.kind.toLowerCase());
 const landCover:AnalysisContext['landCover']=nearestIndustrial&&nearestIndustrial.distanceKm<=2?'industrial':nearbyKinds.some(kind=>kind.includes('forest')||kind.includes('wood'))?'forest':nearbyKinds.some(kind=>kind.includes('residential'))?'urban':'unknown';
 return {landCover,industrialDistanceKm:nearestIndustrial?.distanceKm??null,windKph:Number.isFinite(weather?.windKph)?Number(weather?.windKph):null,weather:weather?{...weather}:null};
}

function humidityLabel(value:number|null){return value===null?'Unavailable':value<20?'Very Dry':value<35?'Dry':value<65?'Moderate':'Humid';}
function windLabel(value:number|null){return value===null?'Unavailable':value<10?'Calm':value<25?'Moderate':value<45?'Strong':'Very Strong';}
function rainLabel(value:number|null){return value===null?'Unavailable':value===0?'No Rain':value<2.5?'Light Rain':value<7.5?'Moderate Rain':'Heavy Rain';}
function weatherInterpretation(weather:Weather){
 const dry=weather.humidityPercent!==null&&weather.humidityPercent<35;
 const windy=weather.windKph!==null&&weather.windKph>=25;
 const wet=(weather.rainMm??weather.precipitationMm??0)>=2.5;
 if(wet)return 'Recent precipitation may reduce immediate vegetation fire-spread conditions. Weather does not identify the thermal source.';
 if(dry&&windy)return 'Dry air and stronger winds may increase potential fire-spread concern if this thermal event is an active fire.';
 if(dry)return 'Low humidity can support drier fuels, so local conditions deserve closer verification if the thermal signal is abnormal.';
 if(windy)return 'Stronger winds could increase spread concern if an active fire is present. The weather itself does not confirm a fire.';
 return 'Current weather adds context to the thermal signal but does not confirm its cause.';
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
 return <section className="ws-panel"><div className="ws-panel-head"><h2>Nearby industry & geography</h2><span className="ws-kicker">OPENSTREETMAP · 5 KM + LIVE WEATHER</span></div><p role="status">{status}</p>{data&&<><p>{data.limitations}</p>{data.warning&&<div className="ws-notice">{data.warning}</div>}{data.weather&&<><div className="ws-evidence weather-evidence"><article className="ws-evidence-item"><span>Temperature</span><strong>{data.weather.temperatureC===null?'Unavailable':`${data.weather.temperatureC.toFixed(1)} °C`}</strong></article><article className="ws-evidence-item"><span>Humidity</span><strong>{data.weather.humidityPercent===null?'Unavailable':`${data.weather.humidityPercent.toFixed(0)}%`}</strong><p>{humidityLabel(data.weather.humidityPercent)}</p></article><article className="ws-evidence-item"><span>Wind</span><strong>{data.weather.windKph===null?'Unavailable':`${data.weather.windKph.toFixed(1)} km/h ${data.weather.windDirectionLabel??''}`.trim()}</strong><p>{windLabel(data.weather.windKph)}{data.weather.windGustKph===null?'':` · gusts ${data.weather.windGustKph.toFixed(1)} km/h`}</p></article><article className="ws-evidence-item"><span>Rain</span><strong>{data.weather.rainMm===null?'Unavailable':`${data.weather.rainMm.toFixed(1)} mm`}</strong><p>{rainLabel(data.weather.rainMm)}</p></article></div><div className="ws-notice"><strong>Weather interpretation:</strong> {weatherInterpretation(data.weather)}</div>{data.weather.forecast24h&&<details><summary>Next 24 hours</summary><p>Temperature: {data.weather.forecast24h.minTemperatureC?.toFixed(1)??'—'}–{data.weather.forecast24h.maxTemperatureC?.toFixed(1)??'—'} °C · Minimum humidity: {data.weather.forecast24h.minHumidityPercent?.toFixed(0)??'—'}% · Max wind: {data.weather.forecast24h.maxWindKph?.toFixed(1)??'—'} km/h · Max gust: {data.weather.forecast24h.maxWindGustKph?.toFixed(1)??'—'} km/h · Expected rain: {data.weather.forecast24h.rainTotalMm?.toFixed(1)??'—'} mm</p></details>}<p className="ws-source">Weather source: <a href={data.weather.sourceUrl} target="_blank" rel="noreferrer">Open-Meteo ↗</a>. Weather is contextual evidence, not confirmation of a fire.</p></>}<div className="ws-evidence">{data.features.map(feature=><article className="ws-evidence-item" key={feature.id}><span>{feature.industrial?'Potential industrial heat context':'Geographic context'}</span><strong>{feature.name}</strong><p>{feature.kind} · {feature.distanceKm.toFixed(2)} km to mapped centre</p><a href={`https://www.openstreetmap.org/${feature.id}`} target="_blank" rel="noreferrer">Inspect mapped feature ↗</a></article>)}</div>{!data.features.length&&<p>No matching mapped features were returned inside 5 km. This is different from a provider failure: OpenStreetMap coverage can be incomplete, so industrial and land-cover context remain unknown unless you verify them manually.</p>}<p className="ws-source">© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap contributors</a> · retrieved {new Date(data.fetchedAt).toLocaleString()}. {source==='demo'?'The thermal history is simulated even though external context is live. ':''}Mapped context is evidence, not verified facility containment or operating status; you can override it before analysis.</p></>}<button className="ws-button" disabled={!selected} onClick={()=>setAttempt(value=>value+1)}>Retry context lookup</button></section>;
}
