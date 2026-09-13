import {useCallback,useEffect,useRef,useState} from 'react';
import {validateObservations,type Observation} from '../ai/thermalEngine';
export interface FirmsFeed {observations:(Observation&{sensor?:string;confidence?:string})[];fetchedAt:string;latestObservation:string|null;sourceUrl:string;sensor:string;windowHours:number;coverage:string;stale:boolean;cached:boolean;warning?:string;}
export function useFirmsFeed(sensor:string,hours:number,automatic:boolean){
 const [feed,setFeed]=useState<FirmsFeed|null>(null);const [loading,setLoading]=useState(false);const [error,setError]=useState('');const controller=useRef<AbortController|null>(null);const sequence=useRef(0);
 const refresh=useCallback(async()=>{
  const request=++sequence.current;controller.current?.abort();const abort=new AbortController();controller.current=abort;setLoading(true);setError('');
  const timeout=setTimeout(()=>abort.abort('timeout'),35000);
  try{
   const response=await fetch(`/api/firms?sensor=${encodeURIComponent(sensor)}&hours=${hours}`,{signal:abort.signal});
   if(!response.headers.get('content-type')?.includes('application/json'))throw new Error('The live-feed service did not respond. Check that the AGNITE app server is running.');
   const data=await response.json();
   if(!response.ok)throw new Error(typeof data.error==='string'?data.error:'NASA FIRMS could not be loaded.');
   if(!Array.isArray(data.observations)||!Number.isFinite(Date.parse(data.fetchedAt))||data.sensor!==sensor||data.windowHours!==hours||typeof data.stale!=='boolean'||typeof data.cached!=='boolean')throw new Error('The feed returned an unexpected response. Please retry.');
   if(data.observations.length)validateObservations(data.observations);
   if(data.observations.some((row:Observation)=>row.source!=='firms'))throw new Error('The feed returned observations without NASA provenance.');
   if(request===sequence.current&&!abort.signal.aborted)setFeed(data);
  }catch(reason){if(request===sequence.current&&(!abort.signal.aborted||abort.signal.reason==='timeout'))setError(abort.signal.reason==='timeout'?'The live-feed request timed out. Please retry.':reason instanceof Error?reason.message:'Feed unavailable.');}
  finally{clearTimeout(timeout);if(request===sequence.current)setLoading(false);}
 },[sensor,hours]);
 useEffect(()=>{setFeed(null);void refresh();return()=>{sequence.current++;controller.current?.abort();};},[refresh]);
 useEffect(()=>{if(!automatic)return;const timer=setInterval(()=>{if(!document.hidden)void refresh();},600000);return()=>clearInterval(timer);},[automatic,refresh]);
 return {feed,loading,error,refresh};
}
