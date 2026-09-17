import { distanceKm } from './notifications.mjs';

const OVERPASS_ENDPOINTS = [
  'https://overpass-api.de/api/interpreter',
  'https://overpass.kumi.systems/api/interpreter',
  'https://overpass.private.coffee/api/interpreter',
  'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
];
const OPEN_METEO_URL = 'https://api.open-meteo.com/v1/forecast';
const MAX_CONTEXT_BYTES = 2_000_000;
const MAX_WEATHER_BYTES = 256_000;
const CACHE_TTL_MS = 15 * 60 * 1000;

const LIMITATIONS = 'Community map coverage may be incomplete. Distances use mapped points or feature centres, not facility boundaries. Nearby features do not establish containment, operational status or fire cause. No mapped industry does not mean no industry exists.';

export function summarizeSiteContext(data, latitude, longitude) {
  if (!Array.isArray(data?.elements) || data.remark) throw Error('Incomplete map response');
  const features=data.elements.flatMap(item=>{
    const point=item.center||item;
    if (!Number.isFinite(point.lat)||!Number.isFinite(point.lon)) return [];
    const tags=item.tags||{};
    return [{id:`${item.type}/${item.id}`,name:tags.name||tags['name:en']||'Unnamed mapped feature',kind:tags.industrial||tags.power||tags.man_made||tags.landuse||tags.natural||'mapped feature',industrial:tags.landuse==='industrial'||!!tags.industrial||['plant','generator'].includes(tags.power)||['works','kiln','chimney'].includes(tags.man_made),distanceKm:distanceKm({latitude,longitude},{latitude:point.lat,longitude:point.lon}),latitude:point.lat,longitude:point.lon}];
  }).sort((a,b)=>a.distanceKm-b.distanceKm);
  return {latitude,longitude,features:features.slice(0,30),source:'OpenStreetMap / Overpass',sourceUrl:'https://www.openstreetmap.org/copyright',radiusKm:5,fetchedAt:new Date().toISOString(),limitations:LIMITATIONS};
}

async function readBoundedJson(response, maxBytes = MAX_CONTEXT_BYTES) {
  const declared=Number(response.headers.get('content-length'));
  if(Number.isFinite(declared)&&declared>maxBytes){await response.body?.cancel();throw Error('Provider response too large.');}
  if(!response.body) throw Error('Provider returned no body.');
  const reader=response.body.getReader();let bytes=0,text='';
  try{
    const decoder=new TextDecoder();
    while(true){
      const {done,value}=await reader.read();if(done)break;
      bytes+=value.byteLength;if(bytes>maxBytes)throw Error('Provider response too large.');
      text+=decoder.decode(value,{stream:true});
    }
    text+=decoder.decode();
  } finally {
    await reader.cancel().catch(()=>{});reader.releaseLock();
  }
  return JSON.parse(text);
}

async function loadWeather(fetchImpl, latitude, longitude) {
  try {
    const params=new URLSearchParams({
      latitude:String(latitude),longitude:String(longitude),
      current:'temperature_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m',
      wind_speed_unit:'kmh',timezone:'auto',forecast_days:'1',
    });
    const response=await fetchImpl(`${OPEN_METEO_URL}?${params}`,{
      method:'GET',redirect:'error',headers:{Accept:'application/json','User-Agent':'AGNITE/0.2 (+https://agnite.onrender.com)'},signal:AbortSignal.timeout(9000),
    });
    if(!response.ok){await response.body?.cancel();return null;}
    const data=await readBoundedJson(response,MAX_WEATHER_BYTES);
    const current=data?.current;
    if(!current||!Number.isFinite(current.wind_speed_10m))return null;
    return {
      source:'Open-Meteo',sourceUrl:'https://open-meteo.com/',observedAt:typeof current.time==='string'?current.time:null,
      windKph:current.wind_speed_10m,
      windDirectionDeg:Number.isFinite(current.wind_direction_10m)?current.wind_direction_10m:null,
      windGustKph:Number.isFinite(current.wind_gusts_10m)?current.wind_gusts_10m:null,
      temperatureC:Number.isFinite(current.temperature_2m)?current.temperature_2m:null,
    };
  } catch {return null;}
}

async function loadMappedContext(fetchImpl, latitude, longitude) {
  const key=`${latitude.toFixed(4)},${longitude.toFixed(4)}`;
  // Keep the query focused on features that materially help thermal interpretation.
  // Residential search uses a smaller radius to avoid huge city responses from public Overpass instances.
  const query=`[out:json][timeout:10];(nwr(around:5000,${key})[landuse=industrial];nwr(around:5000,${key})[industrial];nwr(around:5000,${key})[power~"^(plant|generator)$"];nwr(around:5000,${key})[man_made~"^(works|kiln|chimney)$"];nwr(around:5000,${key})[landuse=forest];nwr(around:5000,${key})[natural=wood];nwr(around:2000,${key})[landuse=residential];);out center tags 80;`;
  for(const endpoint of OVERPASS_ENDPOINTS){
    try{
      const response=await fetchImpl(endpoint,{method:'POST',redirect:'error',headers:{'Content-Type':'application/x-www-form-urlencoded','User-Agent':'AGNITE/0.2 (+https://agnite.onrender.com)'},body:new URLSearchParams({data:query}),signal:AbortSignal.timeout(12000)});
      if(!response.ok){await response.body?.cancel();continue;}
      return summarizeSiteContext(await readBoundedJson(response),latitude,longitude);
    } catch {
      // Public Overpass instances can be busy or rate-limited. Try the next provider.
    }
  }
  return null;
}

export function createSiteContext({fetchImpl=fetch,now=Date.now}={}) {
  const cache=new Map(), pending=new Map();
  return async function get(latitude,longitude) {
    if (!Number.isFinite(latitude)||!Number.isFinite(longitude)||latitude<6||latitude>38||longitude<67||longitude>99) throw Error('Select coordinates within the India region.');
    const key=`${latitude.toFixed(4)},${longitude.toFixed(4)}`;
    const previous=cache.get(key); if (previous&&now()-previous.time<CACHE_TTL_MS) return previous.value;
    if (pending.has(key)) return pending.get(key);
    if (pending.size>=5) throw Error('Map context is busy. Retry shortly.');
    const work=(async()=>{
      const [mapped,weather]=await Promise.all([
        loadMappedContext(fetchImpl,latitude,longitude),
        loadWeather(fetchImpl,latitude,longitude),
      ]);
      if(!mapped&&!weather&&previous) return {...previous.value,stale:true,warning:'Live context providers could not refresh; showing cached location context.'};
      const warnings=[];
      if(!mapped)warnings.push('OpenStreetMap context is temporarily unavailable or rate-limited. Thermal analysis can continue; mapped industry/land-cover remains unknown until a later retry.');
      if(!weather)warnings.push('Current wind/weather context could not be loaded from Open-Meteo.');
      const value={
        ...(mapped||{latitude,longitude,features:[],source:'OpenStreetMap / Overpass',sourceUrl:'https://www.openstreetmap.org/copyright',radiusKm:5,fetchedAt:new Date(now()).toISOString(),limitations:LIMITATIONS}),
        weather,
        ...(warnings.length?{warning:warnings.join(' ')}:{}),
      };
      if(cache.size>=100)cache.delete(cache.keys().next().value);
      cache.set(key,{time:now(),value});
      return value;
    })();
    pending.set(key,work);try{return await work;}finally{pending.delete(key);}
  };
}
