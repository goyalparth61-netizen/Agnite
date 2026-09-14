import { distanceKm } from './notifications.mjs';
export function summarizeSiteContext(data, latitude, longitude) {
  if (!Array.isArray(data?.elements) || data.remark) throw Error('Incomplete map response');
  const features=data.elements.flatMap(item=>{
    const point=item.center||item;
    if (!Number.isFinite(point.lat)||!Number.isFinite(point.lon)) return [];
    const tags=item.tags||{};
    return [{id:`${item.type}/${item.id}`,name:tags.name||tags['name:en']||'Unnamed mapped feature',kind:tags.industrial||tags.power||tags.man_made||tags.landuse||tags.natural||'mapped feature',industrial:tags.landuse==='industrial'||!!tags.industrial||['plant','generator'].includes(tags.power)||['works','kiln','chimney'].includes(tags.man_made),distanceKm:distanceKm({latitude,longitude},{latitude:point.lat,longitude:point.lon}),latitude:point.lat,longitude:point.lon}];
  }).sort((a,b)=>a.distanceKm-b.distanceKm);
  return {latitude,longitude,features:features.slice(0,30),source:'OpenStreetMap / Overpass',sourceUrl:'https://www.openstreetmap.org/copyright',radiusKm:5,fetchedAt:new Date().toISOString(),limitations:'Community map coverage may be incomplete. Distances use mapped points or feature centres, not facility boundaries. Nearby features do not establish containment, operational status or fire cause. No mapped industry does not mean no industry exists.'};
}
export function createSiteContext({fetchImpl=fetch,now=Date.now}={}) {
  const cache=new Map(), pending=new Map();
  return async function get(latitude,longitude) {
    if (!Number.isFinite(latitude)||!Number.isFinite(longitude)||latitude<6||latitude>38||longitude<67||longitude>99) throw Error('Select coordinates within the India region.');
    const key=`${latitude.toFixed(4)},${longitude.toFixed(4)}`;
    const previous=cache.get(key); if (previous&&now()-previous.time<3600000) return previous.value;
    if (pending.has(key)) return pending.get(key);
    if (pending.size>=3) throw Error('Map context is busy. Retry shortly.');
    const work=(async()=>{
      const query=`[out:json][timeout:18];(nwr(around:5000,${key})[landuse~"^(industrial|forest|residential)$"];nwr(around:5000,${key})[industrial];nwr(around:5000,${key})[power~"^(plant|generator)$"];nwr(around:5000,${key})[man_made~"^(works|kiln|chimney)$"];nwr(around:5000,${key})[natural~"^(wood|water|scrub)$"];);out center tags 100;`;
      const response=await fetchImpl('https://overpass-api.de/api/interpreter',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({data:query}),signal:AbortSignal.timeout(22000)});
      if(!response.ok){await response.body?.cancel();throw Error('Map context provider unavailable.');}
      let text='';const reader=response.body.getReader();let bytes=0;
      try{const decoder=new TextDecoder();while(true){const {done,value}=await reader.read();if(done)break;bytes+=value.byteLength;if(bytes>2000000)throw Error('Map response too large.');text+=decoder.decode(value,{stream:true});}text+=decoder.decode();}finally{await reader.cancel();reader.releaseLock();}
      const value=summarizeSiteContext(JSON.parse(text),latitude,longitude);
      if(cache.size>=100)cache.delete(cache.keys().next().value);
      cache.set(key,{time:now(),value});return value;
    })();
    pending.set(key,work);try{return await work;}finally{pending.delete(key);}
  };
}
