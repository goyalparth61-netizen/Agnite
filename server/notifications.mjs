import { randomBytes, createHash } from 'node:crypto';
import { mkdir, readFile, writeFile, rename } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';

const DAY = 86400000;
const hash = value => createHash('sha256').update(value).digest('hex');
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const emailValid = value => typeof value === 'string' && value.length <= 254 && /^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(value);
export function distanceKm(a, b) {
  const r = Math.PI / 180;
  const h = Math.sin((a.latitude-b.latitude)*r/2)**2 + Math.cos(a.latitude*r)*Math.cos(b.latitude*r)*Math.sin((a.longitude-b.longitude)*r/2)**2;
  return 12742 * Math.asin(Math.sqrt(Math.min(1,Math.max(0,h))));
}
export function matchingDetections(rows, site, now) {
  return rows.filter(row => row.source === 'firms' && Number.isFinite(row.frp) && row.frp >= site.frp && Date.parse(row.observedAt) <= now && Date.parse(row.observedAt) >= now-DAY && distanceKm(row,site) <= site.radius);
}
export function createNotifications({ firms, env = process.env, fetchImpl = fetch, now = Date.now, storePath = resolve(env.AGNITE_ALERT_STORE || '.agnite/alerts.json') }) {
  let publicUrl;
  try { const url = new URL(env.AGNITE_PUBLIC_URL); if (['http:','https:'].includes(url.protocol)) publicUrl = url.origin; } catch {}
  const enabled = !!(env.AGNITE_EMAIL_API_KEY && env.AGNITE_EMAIL_FROM && publicUrl);
  let queue = Promise.resolve();
  const serial = work => { const next = queue.then(work); queue = next.catch(()=>{}); return next; };
  const limits = new Map();
  let lastCheck = null, lastError = null;
  async function load() {
    try { const data = JSON.parse(await readFile(storePath,'utf8')); if (!Array.isArray(data)) throw Error('Invalid alert store'); const retained=data.filter(s => s.active || now()-s.createdAt < DAY); if (retained.length!==data.length) await save(retained); return retained; }
    catch (e) { if (e.code === 'ENOENT') return []; throw e; }
  }
  async function save(rows) { await mkdir(dirname(storePath),{recursive:true}); await writeFile(`${storePath}.tmp`,JSON.stringify(rows),{mode:0o600}); await rename(`${storePath}.tmp`,storePath); }
  async function send(to, subject, html, key, replyTo) {
    const response = await fetchImpl('https://api.resend.com/emails',{method:'POST',signal:AbortSignal.timeout(15000),headers:{Authorization:`Bearer ${env.AGNITE_EMAIL_API_KEY}`,'Content-Type':'application/json','Idempotency-Key':key},body:JSON.stringify({from:env.AGNITE_EMAIL_FROM,to:[to],subject,html,...(replyTo?{reply_to:replyTo}:{})})});
    if (!response.ok) { await response.body?.cancel(); throw Error('Email provider unavailable. Please retry later.'); }
    await response.body?.cancel();
  }
  async function body(request) { let text=''; for await (const chunk of request) { text+=chunk; if (Buffer.byteLength(text)>8192) throw Error('Request too large.'); } try { return JSON.parse(text); } catch { throw Error('Invalid request.'); } }
  function reply(res,status,data) { res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'}); res.end(JSON.stringify(data)); }
  function limit(key) {
    for (const [k,v] of limits) if (now()-v.start>3600000) limits.delete(k);
    const value=limits.get(key)||{start:now(),count:0};
    if (value.count>=5 || limits.size>=10000 && !limits.has(key)) return false;
    value.count++; limits.set(key,value); return true;
  }
  async function handle(req,res,url) {
    if (url.pathname === '/api/alerts/status' && req.method === 'GET') return reply(res,200,{enabled,contactEnabled:enabled&&emailValid(env.AGNITE_CONTACT_EMAIL),lastCheck,lastError,intervalMinutes:10});
    if (req.method !== 'POST') return reply(res,405,{error:'Use POST for this action.'});
    if (req.headers.origin && publicUrl && req.headers.origin !== publicUrl) return reply(res,403,{error:'Request origin does not match this installation.'});
    if (!enabled) return reply(res,503,{error:'Email delivery is not configured on this installation.'});
    try {
      const data=await body(req);
      if (url.pathname === '/api/alerts/confirm' || url.pathname === '/api/alerts/unsubscribe') {
        if (typeof data.token !== 'string' || !/^[a-f0-9]{64}$/.test(data.token)) return reply(res,400,{error:'Invalid link.'});
        return await serial(async()=>{
          const rows=await load(); const item=rows.find(s=>url.pathname.endsWith('/unsubscribe') ? hash(s.manageToken)===hash(data.token) : s.tokenHash===hash(data.token));
          if (!item) return reply(res,400,{error:'Link expired or subscription already removed.'});
          if (url.pathname.endsWith('/unsubscribe')) { await save(rows.filter(s=>s!==item)); return reply(res,200,{message:'Subscription removed. Your email and saved location have been deleted.'}); }
          item.active=true; item.confirmedAt ||= new Date(now()).toISOString(); await save(rows);
          reply(res,200,{message:'Email confirmed. Nearby NASA detections will be checked every 10 minutes while the server is running.'});
        });
      }
      if (!limit(`ip:${req.socket.remoteAddress}`)) return reply(res,429,{error:'Too many requests. Try again in one hour.'});
      if (!emailValid(data.email) || data.consent !== true) return reply(res,400,{error:'A valid email and explicit consent are required.'});
      const email=data.email.trim().toLowerCase();
      if (!limit(`email:${email}`)) return reply(res,429,{error:'Too many requests for this address. Try again in one hour.'});
      if (url.pathname === '/api/contact') {
        if (!emailValid(env.AGNITE_CONTACT_EMAIL)) return reply(res,503,{error:'Team contact delivery is not configured.'});
        if (typeof data.message !== 'string' || data.message.trim().length<10 || data.message.length>3000) return reply(res,400,{error:'Write a message between 10 and 3,000 characters.'});
        await send(env.AGNITE_CONTACT_EMAIL,'AGNITE project enquiry',`<p>Reply to: ${escape(email)}</p><p>${escape(data.message).replace(/\n/g,'<br>')}</p>`,randomBytes(16).toString('hex'),email);
        return reply(res,200,{message:'Your enquiry was accepted by the email service.'});
      }
      if (url.pathname !== '/api/alerts/subscribe') return reply(res,404,{error:'Route not found.'});
      if (![data.latitude,data.longitude,data.radius,data.frp].every(Number.isFinite) || data.latitude<6 || data.latitude>38 || data.longitude<67 || data.longitude>99 || data.radius<1 || data.radius>500 || data.frp<0 || data.frp>1000000) return reply(res,400,{error:'Choose an India-region location, radius 1–500 km and FRP 0–1,000,000 MW.'});
      await serial(async()=>{
        const rows=await load(); if (rows.length>=1000) throw Error('Subscription capacity reached.');
        const token=randomBytes(32).toString('hex');
        const item={email,latitude:data.latitude,longitude:data.longitude,radius:data.radius,frp:data.frp,active:false,createdAt:now(),tokenHash:hash(token),manageToken:randomBytes(32).toString('hex'),sent:[]};
        // Persist before sending; never report success without durable consent state.
        await save([...rows,item]);
        const link=`${publicUrl}/#/email-alerts?token=${token}`;
        try { await send(email,'Confirm your AGNITE thermal alerts',`<h1>Confirm nearby thermal alerts</h1><p>You requested NASA detections within ${data.radius} km of ${data.latitude}, ${data.longitude}, with FRP at least ${data.frp} MW. These are detections, not confirmed emergencies.</p><p><a href="${link}">Review and confirm subscription</a></p><p>This link expires after 24 hours. If you did not request this, ignore this email.</p><p><a href="${publicUrl}/#/email-alerts?token=${item.manageToken}&action=unsubscribe">Cancel or unsubscribe and delete this location</a></p>`,item.tokenHash); }
        catch(e) { await save(rows); throw e; }
      });
      return reply(res,202,{message:'Check your inbox to confirm. Monitoring starts only after confirmation.'});
    } catch(e) { return reply(res,400,{error:e.message==='Email provider unavailable. Please retry later.'?e.message:'Could not save this request. Check the fields or retry later.'}); }
  }
  async function tick() {
    if (!enabled) return;
    return serial(async()=>{
      try {
        const rows=await load(); if (!rows.some(s=>s.active)) return;
        const feed=await firms.get({sensor:'noaa20',hours:24});
        if (feed.stale) throw Error('Stale NASA feed; email checks paused.');
        for (const site of rows.filter(s=>s.active)) {
          const key=row=>hash(`${row.latitude}:${row.longitude}:${row.observedAt}`);
          const matches=matchingDetections(feed.observations,site,now()).filter(row=>!site.sent.includes(key(row)));
          if (!matches.length) continue;
          const peak=matches.reduce((a,b)=>a.frp>b.frp?a:b);
          const manage=site.manageToken;
          const management=`${publicUrl}/#/email-alerts?token=${manage}&action=unsubscribe`;
          const previousHash=site.tokenHash;
          // Idempotency uses stable subscription and acquisition IDs.
          const emailKey=hash(`${previousHash}:${matches.map(key).sort().join(',')}`);
          await send(site.email,`AGNITE: ${matches.length} nearby thermal detections`, `<div style="font-family:Arial;border:2px solid #e6b477;padding:24px"><h1>▲ Nearby thermal activity</h1><p>${matches.length} new detections within ${site.radius} km exceeded your ${site.frp} MW threshold.</p><h2>Peak ${peak.frp} MW</h2><p>${escape(peak.observedAt)} UTC<br>${peak.latitude}, ${peak.longitude}</p><p>Reason: measured NASA FIRMS FRP and distance thresholds. Routine industrial heat may also trigger this notice; this is not a confirmed fire or a fire-probability estimate.</p><p><a href="${publicUrl}/#/workspace?tab=monitoring">Inspect NASA observations</a></p><p><a href="${management}">Unsubscribe and delete saved location</a></p></div>`,emailKey);
          site.sent=[...site.sent,...matches.map(key)].slice(-5000); await save(rows);
        }
        lastCheck=new Date(now()).toISOString(); lastError=null;
      } catch { lastError='Alert check failed. Delivery will retry on the next check.'; }
    });
  }
  return {handle,tick,enabled};
}
