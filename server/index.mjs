import { createServer as createHttpServer } from 'node:http';
import {createAiProvider, handleAiRequest} from './aiProvider.mjs';
import { createReadStream } from 'node:fs';
import { realpath, stat } from 'node:fs/promises';
import { dirname, extname, isAbsolute, relative, resolve, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const COVERAGE = 'India region bounding box, includes neighboring areas';
export const CACHE_TTL_MS = 10 * 60 * 1000;
export const MAX_BODY_BYTES = 10 * 1024 * 1024;
export const MAX_OBSERVATIONS = 50_000;
const REQUEST_TIMEOUT_MS = 25_000;
const INDIA_REGION = { west: 67, east: 99, south: 6, north: 38 };
const SENSOR_PATHS = {
  snpp: ['viirs', 'SUOMI_VIIRS_C2'],
  noaa20: ['noaa-20-viirs-c2', 'J1_VIIRS_C2'],
  modis: ['modis-c6.1', 'MODIS_C6_1'],
};
const WINDOWS = { 24: '24h', 48: '48h', 168: '7d' };

export class FirmsError extends Error {
  constructor(message, status = 502) {
    super(message);
    this.name = 'FirmsError';
    this.status = status;
  }
}

export function validateQuery(searchParams) {
  for (const key of searchParams.keys()) {
    if (!['hours', 'sensor'].includes(key) || searchParams.getAll(key).length !== 1) {
      throw new FirmsError('Only one hours and one sensor parameter are supported.', 400);
    }
  }
  const hours = searchParams.get('hours') ?? '24';
  const sensor = searchParams.get('sensor') ?? 'snpp';
  if (!Object.hasOwn(WINDOWS, hours) || !Object.hasOwn(SENSOR_PATHS, sensor)) {
    throw new FirmsError('Use hours=24, 48, or 168 and sensor=snpp, noaa20, or modis.', 400);
  }
  return { hours: Number(hours), sensor };
}

export function sourceUrlFor(sensor, hours) {
  if (!Object.hasOwn(SENSOR_PATHS, sensor) || !Object.hasOwn(WINDOWS, hours)) {
    throw new FirmsError('Unsupported NASA FIRMS source or time window.', 400);
  }
  const [folder, prefix] = SENSOR_PATHS[sensor];
  return `https://firms.modaps.eosdis.nasa.gov/data/active_fire/${folder}/csv/${prefix}_South_Asia_${WINDOWS[hours]}.csv`;
}

// A bounded CSV reader: quoted fields, escaped quotes, BOM and CRLF are supported.
// Malformed documents are rejected instead of being interpreted as observations.
function parseCsv(text) {
  if (Buffer.byteLength(text, 'utf8') > MAX_BODY_BYTES) {
    throw new FirmsError('NASA FIRMS response exceeded the 10 MB safety limit.');
  }
  const rows = [];
  let row = [], field = '', quoted = false, closedQuote = false;
  const pushField = () => {
    row.push(field);
    if (row.length > 128) throw new FirmsError('NASA FIRMS returned an invalid CSV row.');
    field = '';
    closedQuote = false;
  };
  const pushRow = () => {
    pushField();
    if (row.some((value) => value.trim() !== '')) rows.push(row);
    row = [];
  };
  const csv = text.replace(/^\uFEFF/, '');
  for (let index = 0; index < csv.length; index += 1) {
    const character = csv[index];
    if (quoted) {
      if (character === '"') {
        if (csv[index + 1] === '"') { field += '"'; index += 1; }
        else { quoted = false; closedQuote = true; }
      } else field += character;
    } else if (character === ',') pushField();
    else if (character === '\n' || character === '\r') {
      if (character === '\r' && csv[index + 1] === '\n') index += 1;
      pushRow();
    } else if (character === '"' && field.length === 0 && !closedQuote) quoted = true;
    else if (closedQuote || character === '"') {
      throw new FirmsError('NASA FIRMS returned malformed CSV quoting.');
    } else field += character;
    if (field.length > 4096) throw new FirmsError('NASA FIRMS returned an oversized CSV field.');
  }
  if (quoted) throw new FirmsError('NASA FIRMS returned an unfinished CSV field.');
  if (field.length || row.length || closedQuote) pushRow();
  return rows;
}

function finiteNumber(value, minimum, maximum) {
  if (typeof value !== 'string' || !/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(value.trim())) return null;
  const number = Number(value);
  return Number.isFinite(number) && number >= minimum && number <= maximum ? number : null;
}

function acquisitionTime(date, time) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !/^\d{1,4}$/.test(time)) return null;
  const padded = time.padStart(4, '0');
  const hours = Number(padded.slice(0, 2));
  const minutes = Number(padded.slice(2));
  if (hours > 23 || minutes > 59) return null;
  const iso = `${date}T${padded.slice(0, 2)}:${padded.slice(2)}:00.000Z`;
  const timestamp = Date.parse(iso);
  if (!Number.isFinite(timestamp) || new Date(timestamp).toISOString() !== iso) return null;
  return { observedAt: iso, timestamp };
}

export function parseFirmsCsv(text, { sensor = 'snpp', hours = 24, now = Date.now(), maxObservations = MAX_OBSERVATIONS } = {}) {
  sourceUrlFor(sensor, hours);
  const rows = parseCsv(text);
  if (!rows.length) throw new FirmsError('NASA FIRMS returned an empty document instead of CSV.');
  const header = rows.shift().map((name) => name.trim().toLowerCase());
  const required = ['latitude', 'longitude', 'acq_date', 'acq_time', 'frp'];
  if (new Set(header).size !== header.length || required.some((name) => !header.includes(name))) {
    throw new FirmsError('NASA FIRMS response is missing required CSV columns.');
  }
  const columns = Object.fromEntries(header.map((name, index) => [name, index]));
  const observations = [];
  const seen = new Set();
  const skipped = { invalid: 0, outsideRegion: 0, outsideWindow: 0, duplicates: 0, overLimit: 0 };
  const limit = Math.max(1, Math.min(MAX_OBSERVATIONS, maxObservations));
  for (const row of rows) {
    const value = (name) => row[columns[name]]?.trim() ?? '';
    const latitude = finiteNumber(value('latitude'), -90, 90);
    const longitude = finiteNumber(value('longitude'), -180, 180);
    const frp = finiteNumber(value('frp'), 0, 1_000_000);
    const acquisition = acquisitionTime(value('acq_date'), value('acq_time'));
    if (row.length !== header.length || latitude === null || longitude === null || frp === null || !acquisition || acquisition.timestamp > now + 10 * 60 * 1000) {
      skipped.invalid += 1;
      continue;
    }
    if (latitude < INDIA_REGION.south || latitude > INDIA_REGION.north || longitude < INDIA_REGION.west || longitude > INDIA_REGION.east) {
      skipped.outsideRegion += 1;
      continue;
    }
    if (acquisition.timestamp < now - hours * 60 * 60 * 1000) {
      skipped.outsideWindow += 1;
      continue;
    }
    const satellite = value('satellite').slice(0, 20);
    const id = `firms-${sensor}-${satellite}-${latitude.toFixed(5)}-${longitude.toFixed(5)}-${acquisition.observedAt}`;
    const brightnessText = value(Object.hasOwn(columns, 'bright_ti4') ? 'bright_ti4' : 'brightness');
    const brightness = brightnessText ? finiteNumber(brightnessText, 0, 10_000) : undefined;
    const confidenceText = value('confidence');
    let confidence;
    if (/^(l|low|n|nominal|h|high)$/i.test(confidenceText)) confidence = confidenceText.toLowerCase();
    else if (confidenceText) confidence = finiteNumber(confidenceText, 0, 100);
    if (brightness === null || confidence === null) { skipped.invalid += 1; continue; }
    if (seen.has(id)) { skipped.duplicates += 1; continue; }
    seen.add(id);
    if (observations.length >= limit) { skipped.overLimit += 1; continue; }
    observations.push({
      id, latitude, longitude, observedAt: acquisition.observedAt, frp,
      ...(brightness !== undefined ? { brightness } : {}),
      source: 'firms', sensor,
      ...(confidence !== undefined ? { confidence } : {}),
    });
  }
  observations.sort((left, right) => right.observedAt.localeCompare(left.observedAt) || left.id.localeCompare(right.id));
  const notes = [];
  if (skipped.invalid) notes.push(`${skipped.invalid} invalid rows skipped`);
  if (skipped.outsideRegion) notes.push(`${skipped.outsideRegion} detections outside the India region bounding box excluded`);
  if (skipped.outsideWindow) notes.push(`${skipped.outsideWindow} detections outside the selected time window excluded`);
  if (skipped.duplicates) notes.push(`${skipped.duplicates} duplicate detections removed`);
  if (skipped.overLimit) notes.push(`${skipped.overLimit} detections omitted by the ${limit.toLocaleString('en-US')} record limit`);
  // A corrupt non-empty feed must never masquerade as an empty, healthy region.
  if (rows.length && skipped.invalid === rows.length) throw new FirmsError('NASA FIRMS returned no valid CSV records.');
  return {
    observations,
    latestObservation: observations[0]?.observedAt ?? null,
    ...(notes.length ? { warning: `${notes.join('; ')}.` } : {}),
    skipped,
  };
}

async function readBoundedResponse(response) {
  const declaredLength = Number(response.headers.get('content-length'));
  if (Number.isFinite(declaredLength) && declaredLength > MAX_BODY_BYTES) {
    await response.body?.cancel();
    throw new FirmsError('NASA FIRMS response exceeded the 10 MB safety limit.');
  }
  if (!response.body) throw new FirmsError('NASA FIRMS returned no response body.');
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8', { fatal: true });
  let size = 0, text = '';
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_BODY_BYTES) throw new FirmsError('NASA FIRMS response exceeded the 10 MB safety limit.');
      text += decoder.decode(value, { stream: true });
    }
    return text + decoder.decode();
  } catch (error) {
    await reader.cancel().catch(() => {});
    throw error;
  } finally {
    reader.releaseLock();
  }
}

export function createFirmsService({ fetchImpl = fetch, now = Date.now, cacheTtlMs = CACHE_TTL_MS, timeoutMs = REQUEST_TIMEOUT_MS } = {}) {
  const cache = new Map();
  const pending = new Map();
  return {
    async get({ sensor = 'snpp', hours = 24 } = {}) {
      const sourceUrl = sourceUrlFor(sensor, hours);
      const key = `${sensor}:${hours}`;
      const previous = cache.get(key);
      if (previous && now() - previous.timestamp < cacheTtlMs) return { ...previous.result, cached: true };
      if (pending.has(key)) return pending.get(key);
      const refresh = Promise.resolve().then(async () => {
        try {
          const response = await fetchImpl(sourceUrl, {
            signal: AbortSignal.timeout(timeoutMs),
            redirect: 'error',
            headers: { Accept: 'text/csv', 'User-Agent': 'AGNITE/0.1 NASA-FIRMS-public-data' },
          });
          if (!response.ok) {
            await response.body?.cancel();
            throw new FirmsError(`NASA FIRMS download returned HTTP ${response.status}.`);
          }
          const contentType = response.headers.get('content-type')?.toLowerCase() ?? '';
          if (/text\/html|application\/(?:json|xml)/.test(contentType)) {
            await response.body?.cancel();
            throw new FirmsError('NASA FIRMS returned an unexpected response format.');
          }
          const csv = await readBoundedResponse(response);
          const fetched = now();
          const { skipped: _skipped, ...parsed } = parseFirmsCsv(csv, { sensor, hours, now: fetched });
          const result = { ...parsed, fetchedAt: new Date(fetched).toISOString(), sourceUrl, sensor, windowHours: hours, coverage: COVERAGE, stale: false, cached: false };
          cache.set(key, { timestamp: fetched, result });
          return result;
        } catch (error) {
          const reason = error instanceof FirmsError ? error.message : error?.name === 'TimeoutError' || error?.name === 'AbortError' ? 'NASA FIRMS download timed out.' : 'NASA FIRMS could not be reached.';
          if (previous) return {
            ...previous.result, cached: true, stale: true,
            warning: `${reason} Showing cached observations fetched at ${previous.result.fetchedAt}. ${previous.result.warning ?? ''}`.trim(),
          };
          throw new FirmsError(`${reason} No cached observations are available. Retry shortly.`);
        } finally {
          pending.delete(key);
        }
      });
      pending.set(key, refresh);
      return refresh;
    },
  };
}

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.webp': 'image/webp', '.gif': 'image/gif', '.ico': 'image/x-icon',
  '.woff': 'font/woff', '.woff2': 'font/woff2', '.txt': 'text/plain; charset=utf-8',
  '.csv': 'text/csv; charset=utf-8', '.gz': 'application/gzip', '.pdf': 'application/pdf',
};
const defaultDist = resolve(dirname(fileURLToPath(import.meta.url)), '../dist');
const isInside = (root, target) => {
  const relativePath = relative(root, target);
  return relativePath === '' || (!relativePath.startsWith(`..${sep}`) && relativePath !== '..' && !isAbsolute(relativePath));
};
function json(response, status, payload) {
  response.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' });
  response.end(JSON.stringify(payload));
}

export function createServer({ distDir = defaultDist, fetchImpl, now, cacheTtlMs, timeoutMs } = {}) {
  const distRoot = resolve(distDir);
  const ai = createAiProvider();
  const firms = createFirmsService({ fetchImpl, now, cacheTtlMs, timeoutMs });
  return createHttpServer(async (request, response) => {
    try {
      const url = new URL(request.url ?? '/', 'http://localhost');
      if (url.pathname === '/api/agnite/ask') return await handleAiRequest(request, response, ai);
      if (!['GET', 'HEAD'].includes(request.method)) {
        response.setHeader('Allow', 'GET, HEAD');
        return json(response, 405, { error: 'Method not allowed.' });
      }
      if (url.pathname === '/api/health') return json(response, 200, { status: 'ok', service: 'agnite', firms: 'public-nasa-downloads' });
      if (url.pathname === '/api/firms') return json(response, 200, await firms.get(validateQuery(url.searchParams)));
      if (url.pathname.startsWith('/api/')) return json(response, 404, { error: 'API route not found.' });
      let pathname;
      try { pathname = decodeURIComponent(url.pathname); }
      catch { return json(response, 400, { error: 'Invalid path encoding.' }); }
      // Backslashes, colon drive prefixes, dotfiles and any traversal segment are
      // forbidden on every platform. Symlinks are checked by their real paths too.
      if (pathname.includes('\0') || pathname.includes('\\') || pathname.includes(':') || pathname.split('/').some((part) => part === '..' || part.startsWith('.'))) {
        return json(response, 403, { error: 'Path is not allowed.' });
      }
      let target = resolve(distRoot, `.${pathname === '/' ? '/index.html' : pathname}`);
      if (!isInside(distRoot, target)) return json(response, 403, { error: 'Path is not allowed.' });
      let fileStat;
      try { fileStat = await stat(target); }
      catch (error) {
        if (error.code !== 'ENOENT' && error.code !== 'ENOTDIR') throw error;
        if (!extname(pathname) && !pathname.startsWith('/data/') && request.headers.accept?.includes('text/html')) {
          target = resolve(distRoot, 'index.html');
          fileStat = await stat(target).catch(() => null);
        }
      }
      if (!fileStat?.isFile()) return json(response, 404, { error: 'File not found. Run npm run build to generate the application.' });
      const [realRoot, realTarget] = await Promise.all([realpath(distRoot), realpath(target)]);
      if (!isInside(realRoot, realTarget)) return json(response, 403, { error: 'Path is not allowed.' });
      response.writeHead(200, {
        'Content-Type': MIME[extname(target).toLowerCase()] ?? 'application/octet-stream',
        'Content-Length': fileStat.size,
        'Cache-Control': pathname.startsWith('/assets/') ? 'public, max-age=31536000, immutable' : 'no-cache',
        'X-Content-Type-Options': 'nosniff',
      });
      if (request.method === 'HEAD') return response.end();
      const stream = createReadStream(realTarget);
      stream.on('error', () => response.destroy());
      response.on('close', () => stream.destroy());
      stream.pipe(response);
    } catch (error) {
      if (response.headersSent) response.destroy();
      else json(response, error instanceof FirmsError ? error.status : 500, { error: error instanceof FirmsError ? error.message : 'The server could not complete this request.' });
    }
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const port = Number(process.env.PORT ?? 8787);
  const host = process.env.HOST ?? '127.0.0.1';
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('PORT must be a valid TCP port.');
  const server = createServer();
  server.listen(port, host, () => {
    console.log(`AGNITE app + NASA FIRMS API: http://${host}:${server.address().port}`);
  });
}
