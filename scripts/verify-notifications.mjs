import assert from 'node:assert/strict';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {Readable} from 'node:stream';
import {createNotifications,matchingDetections} from '../server/notifications.mjs';
import {summarizeSiteContext,createSiteContext} from '../server/siteContext.mjs';
const directory=await mkdtemp(join(tmpdir(),'agnite-alert-test-'));
const now=Date.parse('2026-09-14T12:00:00Z');
const row={id:'nasa-1',latitude:21,longitude:79,observedAt:new Date(now-3600000).toISOString(),frp:60,source:'firms'};
let stale=false,failEmail=false;
const emails=[];
const storePath=join(directory,'alerts.json');
const options={firms:{get:async()=>({observations:[row],stale})},env:{AGNITE_EMAIL_API_KEY:'test-only',AGNITE_EMAIL_FROM:'test@example.com',AGNITE_PUBLIC_URL:'https://agnite.example',AGNITE_CONTACT_EMAIL:'team@example.com'},storePath,now:()=>now,fetchImpl:async(url,options)=>{assert.equal(url,'https://api.resend.com/emails');if(failEmail)return new Response('',{status:503});emails.push(JSON.parse(options.body));return new Response('{}');}};
let service=createNotifications(options);
async function call(path,data,method='POST',origin='https://agnite.example') {
 const req=Readable.from([JSON.stringify(data)]);req.method=method;req.headers={origin};req.socket={remoteAddress:'test'};
 let status,payload;const res={writeHead(code){status=code;},end(body){payload=JSON.parse(body);}};
 await service.handle(req,res,new URL(path,'https://agnite.example'));return {status,...payload};
}
try {
 const input={email:'person@example.com',latitude:21,longitude:79,radius:25,frp:20,consent:true};
 assert.equal((await call('/api/alerts/status',{},'GET')).enabled,true);
 assert.equal((await call('/api/alerts/subscribe',{...input,consent:false})).status,400);
 assert.equal((await call('/api/alerts/subscribe',input,'POST','https://other.example')).status,403);
 assert.equal((await call('/api/alerts/subscribe',input)).status,202);
 await service.tick();assert.equal(emails.length,1,'Unconfirmed users must not receive detection alerts');
 const token=emails[0].html.match(/token=([a-f0-9]{64})/)[1];
 assert.equal((await call('/api/alerts/confirm',{token:'bad'})).status,400);
 assert.equal((await call('/api/alerts/confirm',{token})).status,200);
 stale=true;await service.tick();assert.equal(emails.length,1,'Stale feeds must not send alerts');
 stale=false;failEmail=true;await service.tick();assert.equal(emails.length,1);
 failEmail=false;await service.tick();assert.equal(emails.length,2,'Failed delivery must retry');
 const management=emails[1].html.match(/token=([a-f0-9]{64})/)[1];
 assert.match(emails[1].html,/not a confirmed fire/);
 await service.tick();assert.equal(emails.length,2,'Same acquisitions must not repeat');
 service=createNotifications(options);await service.tick();assert.equal(emails.length,2,'Dedupe survives restart');
 assert.equal((await call('/api/alerts/unsubscribe',{token:management})).status,200);
 assert.deepEqual(JSON.parse(await readFile(storePath,'utf8')),[],'Unsubscribe removes personal data');
 await service.tick();assert.equal(emails.length,2);
 assert.equal(matchingDetections([row,{...row,source:'demo'},{...row,observedAt:new Date(now+1).toISOString()},{...row,latitude:30}],input,now).length,1);
 const context=summarizeSiteContext({elements:[{type:'way',id:1,center:{lat:21,lon:79},tags:{name:'Test steel works',landuse:'industrial'}},{type:'node',id:2,lat:21.001,lon:79,tags:{natural:'wood'}}]},21,79);
 assert.equal(context.features.length,2);assert.equal(context.features[0].industrial,true);assert.equal(context.features[0].distanceKm,0);
 assert.throws(()=>summarizeSiteContext({elements:[],remark:'timeout'},21,79));
 let requests=0;const lookup=createSiteContext({fetchImpl:async()=>{requests++;return new Response(JSON.stringify({elements:[]}));}});
 await Promise.all([lookup(21,79),lookup(21,79)]);await lookup(21,79);assert.equal(requests,1,'Concurrent and repeated lookups share cache');
 await assert.rejects(()=>lookup(NaN,79));
 console.log('PASS: email consent, confirmation, origin validation, stale-feed suppression, retry, persisted dedupe, unsubscribe deletion, source filtering and mapped context cache. No real emails sent.');
} finally {await rm(directory,{recursive:true,force:true});}
