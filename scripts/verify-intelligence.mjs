import assert from 'node:assert/strict';
import {summarizeLocation,estimateRisk,buildIntelligence} from '../src/ai/intelligence.ts';
import {askAgnite,localAnswer} from '../src/ai/assistantService.ts';
import {createAiProvider} from '../server/aiProvider.mjs';
import {createServer} from '../server/index.mjs';
const context={windKph:null,industrialDistanceKm:null,landCover:'unknown'};
const row=(i,frp)=>({id:String(i),latitude:21,longitude:79,observedAt:new Date(Date.UTC(2026,0,i+1)).toISOString(),frp,source:'manual'});
const rising=[row(0,10),row(1,20),row(2,40)];
const h=summarizeLocation(rising[2],rising);
assert.equal(h.historicalDetections,2);assert.equal(h.baselineFrp,15);assert.equal(h.trend,'rising');assert.equal(h.peakFrp,40);assert.equal(h.averageFrp,70/3);assert.deepEqual(h.gapsHours,[24,24]);assert.equal(h.recurrencePerDay,1);assert.equal(h.persistenceScore,100);
assert.equal(summarizeLocation(null,[]).totalDetections,0);
assert.deepEqual(estimateRisk(summarizeLocation(null,[]),context,null),[]);
const single=summarizeLocation(rising[0],[rising[0]]);assert.equal(single.baselineFrp,null);assert.equal(single.trend,'unknown');assert.equal(single.persistenceScore,null);
assert.equal(summarizeLocation(rising[2],[...rising,...rising,{...row(3,999),latitude:0}]).totalDetections,3);
assert.equal(summarizeLocation(rising[0],rising).totalDetections,1);
assert.equal(summarizeLocation(rising[2],[...rising,{...row(1,500),source:'demo'}]).totalDetections,3);
const falling=[row(0,40),row(1,20),row(2,10)];assert.equal(summarizeLocation(falling[2],falling).trend,'falling');
assert.equal(summarizeLocation(row(1,10),[row(0,0)]).anomalyPercent,null);
for(const frp of [0,1,100,1000000])for(const windKph of [null,0,500]) {
 const predictions=estimateRisk(summarizeLocation(row(2,frp),rising),{...context,windKph},null);
 assert.equal(predictions.length,3);
 for(const p of predictions){assert.ok(p.riskScore>=0&&p.riskScore<=100);assert.equal(p.riskScore,Math.round(Math.max(0,Math.min(100,p.contributingFactors.reduce((s,f)=>s+f.points,0)))));assert.match(p.explanation,/SIMULATION/);}
}
const data=buildIntelligence(rising[2],rising,context,null);
assert.match(localAnswer('Why is next 7-day risk high?',data),/WHY THIS SCORE/);
assert.match(localAnswer('Compare historical baseline',data),/15.0 MW/);
assert.match(localAnswer('Missing evidence',data),/Wind unavailable/);
assert.match(localAnswer('Why is risk high?',data),/WHY THIS SCORE/);
assert.match(localAnswer('Safety precautions',data),/responsible local authorities/);
assert.match(localAnswer('Explain simply',data),/does not confirm a fire/);
assert.match(localAnswer('Explain classification',data),/Run site analysis first/);
assert.match(localAnswer('history',buildIntelligence(null,[],context,null)),/Select a hotspot/);
for(const fetchImpl of [async()=>{throw new Error('offline');},async()=>new Response('{}',{status:503}),async()=>Response.json({mode:'local'}),async()=>new Response('bad json')]) {
 const result=await askAgnite('Future risk',data,fetchImpl);assert.equal(result.mode,'local');assert.match(result.answer,/(?:SIMULATION|REAL-DATA THERMAL RECURRENCE MODEL)/);
}
assert.equal((await createAiProvider({env:{},fetchImpl:()=>{throw new Error('must not fetch');}}).answer('history',data)).mode,'local');
let payload;
const provider=createAiProvider({env:{AGNITE_LLM_API_KEY:'test-only',AGNITE_LLM_BASE_URL:'https://example.test/v1',AGNITE_LLM_MODEL:'test'},fetchImpl:async(url,options)=>{payload=JSON.parse(options.body);assert.equal(url,'https://example.test/v1/chat/completions');return Response.json({choices:[{message:{content:'Grounded test answer'}}]});}});
assert.equal((await provider.answer('history',data)).mode,'provider');assert.match(payload.messages[0].content,/Never invent/);assert.match(payload.messages[1].content,/hotspotContext/);
assert.equal((await createAiProvider({env:{AGNITE_LLM_API_KEY:'test'},fetchImpl:async()=>{throw new Error('provider down');}}).answer('history',data)).mode,'local');
const server=createServer();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
try{const url=`http://127.0.0.1:${server.address().port}/api/agnite/ask`;assert.equal((await fetch(url)).status,405);assert.equal((await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})).status,400);assert.equal((await fetch(url,{method:'POST',headers:{'Content-Type':'application/json',Origin:'https://other.test'},body:'{}'})).status,403);}finally{await new Promise(resolve=>server.close(resolve));}
console.log('PASS: history, temporal/provenance isolation, recurrence, trends, risk bounds/factors, assistant intents, local/network/provider fallback and endpoint validation.');
