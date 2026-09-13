import assert from 'node:assert/strict';
import { once } from 'node:events';
import { mkdtemp, mkdir, writeFile, rm, symlink } from 'node:fs/promises';
import { get as httpGet } from 'node:http';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { gzipSync } from 'node:zlib';
import {
  CACHE_TTL_MS, COVERAGE, MAX_BODY_BYTES, createFirmsService, createServer,
  parseFirmsCsv, sourceUrlFor, validateQuery,
} from '../server/index.mjs';

const NOW = Date.parse('2026-09-13T10:00:00.000Z');
const HEADER = 'latitude,longitude,bright_ti4,acq_date,acq_time,satellite,confidence,frp';
const ROW = '21.1,79.2,340.1,2026-09-13,0930,N,nominal,12.5';
const ROW2 = '22.1,80.2,342.1,2026-09-13,0940,N,high,32.5';
const CSV = `${HEADER}\n${ROW}\n${ROW2}\n`;
const response = (csv = CSV, options = {}) => new Response(csv, { headers: { 'content-type': 'text/csv' }, ...options });
let checks = 0;

function check(name, callback) {
  return Promise.resolve().then(callback).then(() => { checks += 1; console.log(`PASS ${name}`); });
}

await check('normalizes real FIRMS column names, UTC times, provenance and newest-first ordering', () => {
  const result = parseFirmsCsv(CSV, { now: NOW });
  assert.equal(result.observations.length, 2);
  assert.equal(result.latestObservation, '2026-09-13T09:40:00.000Z');
  assert.deepEqual(result.observations[0], {
    id: 'firms-snpp-N-22.10000-80.20000-2026-09-13T09:40:00.000Z',
    latitude: 22.1, longitude: 80.2, observedAt: '2026-09-13T09:40:00.000Z',
    brightness: 342.1, frp: 32.5, source: 'firms', sensor: 'snpp', confidence: 'high',
  });
});

await check('accepts BOM/CRLF/quoted fields, MODIS brightness and numeric confidence', () => {
  const csv = '\uFEFFlatitude,longitude,brightness,acq_date,acq_time,satellite,confidence,frp\r\n"21.1",79.2,320.1,2026-09-13,30,T,76,4.5\r\n';
  const record = parseFirmsCsv(csv, { sensor: 'modis', hours: 24, now: NOW }).observations[0];
  assert.equal(record.observedAt, '2026-09-13T00:30:00.000Z');
  assert.equal(record.confidence, 76);
  assert.equal(record.brightness, 320.1);
  assert.equal(record.sensor, 'modis');
});

await check('rejects blanks, invalid dates/times/ranges, and explicitly reports every excluded record', () => {
  const csv = [HEADER, ROW, ROW,
    ROW.replace('12.5', ''), ROW.replace('21.1', '91'), ROW.replace('0930', '2561'),
    ROW.replace('2026-09-13', '2026-02-30'), ROW.replace('nominal', 'unknown'),
    ROW.replace('340.1', 'Infinity'), ROW.replace('2026-09-13', '2026-09-14'),
    ROW.replace('21.1', '4'), ROW.replace('2026-09-13', '2026-09-10'),
  ].join('\n');
  const result = parseFirmsCsv(csv, { now: NOW });
  assert.equal(result.observations.length, 1);
  assert.deepEqual(result.skipped, { invalid: 7, outsideRegion: 1, outsideWindow: 1, duplicates: 1, overLimit: 0 });
  assert.match(result.warning, /7 invalid rows/);
  assert.match(result.warning, /1 duplicate/);
  assert.match(result.warning, /outside the India region/);
  assert.match(result.warning, /outside the selected time window/);
});

await check('empty legitimate feeds stay empty; malformed or fully invalid feeds fail', () => {
  assert.deepEqual(parseFirmsCsv(`${HEADER}\n`, { now: NOW }).observations, []);
  for (const csv of ['', '<html>error</html>', `${HEADER}\n"unfinished`, `${HEADER}\n${ROW.replace('12.5', '')}`]) {
    assert.throws(() => parseFirmsCsv(csv, { now: NOW }));
  }
  assert.throws(() => parseFirmsCsv('latitude,longitude,frp,acq_date,acq_time,latitude\n', { now: NOW }));
  const capped = parseFirmsCsv(CSV, { now: NOW, maxObservations: 1 });
  assert.equal(capped.observations.length, 1);
  assert.match(capped.warning, /1 detections omitted by the 1 record limit/);
});

await check('query allowlist and fixed NASA URLs prevent arbitrary upstream requests', () => {
  assert.deepEqual(validateQuery(new URLSearchParams()), { sensor: 'snpp', hours: 24 });
  for (const query of ['hours=1', 'hours=024', 'sensor=constructor', 'sensor=__proto__', 'url=https://example.com', 'hours=24&hours=48', 'sensor=snpp&sensor=modis']) {
    assert.throws(() => validateQuery(new URLSearchParams(query)), (error) => error.status === 400);
  }
  for (const sensor of ['snpp', 'noaa20', 'modis']) {
    for (const hours of [24, 48, 168]) {
      const url = new URL(sourceUrlFor(sensor, hours));
      assert.equal(url.origin, 'https://firms.modaps.eosdis.nasa.gov');
      assert.match(url.pathname, /_South_Asia_(24h|48h|7d)\.csv$/);
    }
  }
  assert.throws(() => sourceUrlFor('https://example.com', 24));
});

await check('deduplicates concurrent requests, caches ten minutes and preserves provenance on stale fallback', async () => {
  let clock = NOW, calls = 0, fail = false, release;
  const gate = new Promise((resolve) => { release = resolve; });
  const service = createFirmsService({ now: () => clock, fetchImpl: async (url, options) => {
    calls += 1;
    assert.equal(url, sourceUrlFor('snpp', 24));
    assert.equal(options.redirect, 'error');
    assert.ok(options.signal instanceof AbortSignal);
    await gate;
    if (fail) throw new Error('private network detail must not be exposed');
    return response();
  } });
  const first = service.get(), second = service.get();
  await Promise.resolve();
  assert.equal(calls, 1);
  release();
  const [a, b] = await Promise.all([first, second]);
  assert.deepEqual(a, b);
  assert.equal(a.coverage, COVERAGE);
  assert.equal(a.sourceUrl, sourceUrlFor('snpp', 24));
  assert.equal(a.stale, false);
  assert.equal(a.cached, false);
  clock += 1000;
  assert.equal((await service.get()).cached, true);
  assert.equal(calls, 1);
  clock += CACHE_TTL_MS;
  fail = true;
  const stale = await service.get();
  assert.equal(stale.stale, true);
  assert.equal(stale.cached, true);
  assert.equal(stale.fetchedAt, a.fetchedAt);
  assert.equal(stale.latestObservation, a.latestObservation);
  assert.match(stale.warning, /Showing cached observations/);
  assert.doesNotMatch(stale.warning, /private network detail/);
  fail = false;
  const recovered = await service.get();
  assert.equal(recovered.stale, false);
  assert.notEqual(recovered.fetchedAt, a.fetchedAt);
  assert.equal(calls, 3);
});

await check('upstream failures without cache return errors and never synthetic observations', async () => {
  const failures = [
    async () => new Response('unavailable', { status: 503 }),
    async () => new Response('<html>blocked</html>', { headers: { 'content-type': 'text/html' } }),
    async () => response('not a csv'),
    () => { throw new Error('sync failure'); },
  ];
  for (const fetchImpl of failures) {
    const service = createFirmsService({ now: () => NOW, fetchImpl });
    await assert.rejects(service.get(), (error) => error.status === 502 && /No cached observations/.test(error.message));
    await assert.rejects(service.get(), (error) => error.status === 502);
  }
});

await check('enforces declared and streamed response size limits plus upstream timeout', async () => {
  for (const fetchImpl of [
    async () => response('', { headers: { 'content-type': 'text/csv', 'content-length': String(MAX_BODY_BYTES + 1) } }),
    async () => new Response(new ReadableStream({ start(controller) { controller.enqueue(new Uint8Array(MAX_BODY_BYTES + 1)); controller.close(); } })),
  ]) {
    await assert.rejects(createFirmsService({ fetchImpl }).get(), /10 MB/);
  }
  // Keep the event loop alive while AbortSignal.timeout's unreferenced timer runs.
  const keepAlive = setInterval(() => {}, 1000);
  try {
    const service = createFirmsService({ timeoutMs: 10, fetchImpl: async (_url, { signal }) => new Promise((_resolve, reject) => {
      signal.addEventListener('abort', () => reject(signal.reason), { once: true });
    }) });
    await assert.rejects(service.get(), /timed out/);
  } finally { clearInterval(keepAlive); }
});

const temporary = await mkdtemp(join(tmpdir(), 'agnite-firms-test-'));
let server;
try {
  const dist = join(temporary, 'dist');
  await mkdir(join(dist, 'data'), { recursive: true });
  await mkdir(join(temporary, 'private'));
  await writeFile(join(dist, 'index.html'), '<!doctype html><h1>AGNITE test</h1>');
  await writeFile(join(temporary, 'private', 'secret.txt'), 'SHOULD NEVER BE SERVED');
  await writeFile(join(dist, '.env'), 'SHOULD NEVER BE SERVED');
  const compressed = gzipSync('[{"city":"Nagpur"}]');
  await writeFile(join(dist, 'data', 'cities.json.gz'), compressed);
  await symlink(join(temporary, 'private'), join(dist, 'linked'), process.platform === 'win32' ? 'junction' : 'dir');
  server = createServer({ distDir: dist, now: () => NOW, fetchImpl: async () => response() });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const address = `http://127.0.0.1:${server.address().port}`;
  const rawGet = (path) => new Promise((resolve, reject) => {
    httpGet(`${address}${path}`, (result) => {
      let body = '';
      result.setEncoding('utf8');
      result.on('data', (chunk) => { body += chunk; });
      result.on('end', () => resolve({ status: result.statusCode, body }));
    }).on('error', reject);
  });

  await check('HTTP routes expose health, typed FIRMS data, query errors and allowed methods', async () => {
    assert.equal((await fetch(`${address}/api/health`)).status, 200);
    const live = await (await fetch(`${address}/api/firms?hours=24&sensor=snpp`)).json();
    assert.equal(live.observations.length, 2);
    assert.equal(live.observations[0].source, 'firms');
    assert.equal((await fetch(`${address}/api/firms?hours=72`)).status, 400);
    assert.equal((await fetch(`${address}/api/unknown`)).status, 404);
    const denied = await fetch(`${address}/api/firms`, { method: 'POST' });
    assert.equal(denied.status, 405);
    assert.equal(denied.headers.get('allow'), 'GET, HEAD');
  });

  await check('static serving supports SPA routes and raw gzip without Content-Encoding', async () => {
    const home = await fetch(address);
    assert.match(await home.text(), /AGNITE test/);
    const route = await fetch(`${address}/dashboard`, { headers: { Accept: 'text/html' } });
    assert.equal(route.status, 200);
    const gzip = await fetch(`${address}/data/cities.json.gz`);
    assert.equal(gzip.headers.get('content-type'), 'application/gzip');
    assert.equal(gzip.headers.get('content-encoding'), null);
    assert.deepEqual(Buffer.from(await gzip.arrayBuffer()), compressed);
    const head = await fetch(address, { method: 'HEAD' });
    assert.equal(head.status, 200);
    assert.equal(await head.text(), '');
    assert.equal((await fetch(`${address}/data/missing.json`)).status, 404);
  });

  await check('static paths cannot reveal dotfiles, parent directories or symlinked files', async () => {
    for (const path of ['/.env', '/%2e%2e%2fprivate/secret.txt', '/..%5cprivate%5csecret.txt', '/C%3a/Windows/win.ini', '/linked/secret.txt']) {
      const result = await rawGet(path);
      assert.equal(result.status, 403, path);
      assert.doesNotMatch(result.body, /SHOULD NEVER BE SERVED/);
    }
    assert.equal((await rawGet('/%ZZ')).status, 400);
  });
} finally {
  if (server) await new Promise((resolve, reject) => { server.close((error) => error ? reject(error) : resolve()); server.closeAllConnections(); });
  const cleanupTarget = resolve(temporary);
  assert.equal(dirname(cleanupTarget), resolve(tmpdir()), 'Cleanup must stay inside the temporary directory.');
  assert.ok(cleanupTarget.startsWith(join(resolve(tmpdir()), 'agnite-firms-test-')), 'Cleanup must target this test fixture.');
  await rm(cleanupTarget, { recursive: true, force: true });
}

console.log(`NASA FIRMS server: ${checks} checks passed.`);
