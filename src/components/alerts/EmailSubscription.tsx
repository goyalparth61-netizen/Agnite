import { useEffect, useState, type FormEvent } from 'react';
export default function EmailSubscription({location,radius}:{location:{latitude:number;longitude:number}|null;radius:number}) {
  const [enabled,setEnabled]=useState(false);
  const [status,setStatus]=useState('Checking email availability…');
  const [busy,setBusy]=useState(false);
  useEffect(()=>{const controller=new AbortController(); fetch('/api/alerts/status',{signal:controller.signal}).then(r=>r.json()).then(data=>{setEnabled(data.enabled===true);setStatus(data.enabled?'Confirm your email to activate scheduled checks.':'BACKEND CONNECTION REQUIRED · Email delivery has not been configured.');}).catch(()=>{if(!controller.signal.aborted)setStatus('Email service unavailable. In-app monitoring remains available.');});return()=>controller.abort();},[]);
  async function submit(event:FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!location||busy) return;
    const data=new FormData(event.currentTarget);setBusy(true);
    try { const response=await fetch('/api/alerts/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...location,radius,email:data.get('email'),frp:Number(data.get('frp')),consent:data.get('consent')==='on'}),signal:AbortSignal.timeout(20000)});const result=await response.json();setStatus(result.message||result.error||'Request failed.'); }
    catch {setStatus('Could not reach the email service. Please retry.');} finally {setBusy(false);}
  }
  return <section className="intel-card"><span className="eyebrow">CONFIRMED EMAIL ALERTS</span><h2>Watch this location.</h2><p role="status">{status}</p><form className="alert-form" onSubmit={submit}><label>Email<input name="email" required type="email" maxLength={254} autoComplete="email" placeholder="you@example.com"/></label><label>Minimum FRP (MW)<input name="frp" required type="number" min={0} max={1000000} defaultValue={20}/></label><p>Uses your selected {radius} km radius. Email triggers use measured FRP, not an unvalidated risk percentage.</p><label className="consent-row"><input name="consent" type="checkbox" required/>I agree to store this email and location on the server and receive nearby detection alerts. Unsubscribe deletes this record.</label><button className="button secondary" disabled={!enabled||!location||busy}>{busy?'Submitting…':'Send confirmation email'}</button>{!location&&<p>Enable your optional location first to choose the alert centre.</p>}</form><p>Checks run every 10 minutes while the server is running, using acquisitions from the last 24 hours. Satellite gaps and email delays are possible.</p></section>;
}
