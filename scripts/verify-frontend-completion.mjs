import assert from 'node:assert/strict';
import {createServer} from 'vite';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

// Render real components without browser globals: location must remain opt-in.
const vite = await createServer({cacheDir:join(tmpdir(),'agnite-frontend-render-cache'),optimizeDeps:{noDiscovery:true,include:[]},server:{middlewareMode:true},appType:'custom'});
try {
  const load = path => vite.ssrLoadModule(`/src/${path}`);
  const {buildIntelligence} = await load('ai/intelligence.ts');
  const {sampleObservations} = await load('ai/workspaceData.ts');
  const {analyzeObservations} = await load('ai/thermalEngine.ts');
  const rows=sampleObservations();
  const selected=rows.at(-1);
  const context={landCover:'industrial',industrialDistanceKm:.5,windKph:12};
  const data=buildIntelligence(selected,rows,context,analyzeObservations(rows,context,selected));
  const render=async(path,props={})=>renderToStaticMarkup(React.createElement((await load(path)).default,props));
  const summary=await render('components/intelligence/HotspotSummary.tsx',{data});
  assert.match(summary,/SIMULATED DATA/);
  assert.match(summary,/Detection confidence/);
  assert.match(summary,/Unavailable/);
  for(const [source,label] of [['manual','MANUAL DATA'],['imported','IMPORTED DATA'],['firms','NASA DATA']]) {
    const input={...selected,source};
    assert.match(await render('components/intelligence/HotspotSummary.tsx',{data:buildIntelligence(input,[input],context,null)}),new RegExp(label));
  }
  const risk=await render('components/risk/RiskOverview.tsx',{data});
  for(const text of ['NEXT 24 HOURS','NEXT 48 HOURS','NEXT 7 DAYS','SIMULATION','Contributing factors','SAFETY PRECAUTIONS']) assert.ok(risk.includes(text));
  assert.equal((risk.match(/role="meter"/g)||[]).length,3);
  const alerts=await render('components/alerts/NearbyAlerts.tsx');
  assert.match(alerts,/Enable Nearby Alerts/);
  assert.match(alerts,/Send confirmation email/);
  assert.match(alerts,/Use these coordinates/);
  assert.match(alerts,/type="email"/);
  const docs=await render('components/docs/DocumentationSection.tsx');
  const {documentationLinks,docId}=await load('components/docs/DocumentationSection.tsx');
  for(const label of documentationLinks) assert.ok(docs.includes(`id="${docId(label)}"`));
  assert.match(await render('components/awareness/AwarenessSection.tsx'),/NO LIVE NEWS FEED/);
  console.log('PASS: component rendering, provenance labels, risk windows/meters, optional location, confirmed-email form, documentation anchors and educational labels.');
} finally {await vite.close();}
