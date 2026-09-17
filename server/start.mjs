import { createServer } from './index.mjs';

const nativeFetch = globalThis.fetch;
const MAP_KEY = (process.env.NASA_FIRMS_MAP_KEY ?? '').trim();
const INDIA_BBOX = '67,6,99,38';

const SOURCE_BY_PUBLIC_URL = [
  [/J1_VIIRS_C2/i, 'VIIRS_NOAA20_NRT'],
  [/SUOMI_VIIRS_C2/i, 'VIIRS_SNPP_NRT'],
  [/MODIS_C6_1/i, 'MODIS_NRT'],
];

function dayRangeFromPublicUrl(url) {
  if (/_7d\.csv(?:$|\?)/i.test(url)) return 7;
  if (/_48h\.csv(?:$|\?)/i.test(url)) return 2;
  return 1;
}

function areaApiUrlFor(publicUrl) {
  if (!MAP_KEY || !publicUrl.includes('firms.modaps.eosdis.nasa.gov/data/active_fire/')) return null;
  const source = SOURCE_BY_PUBLIC_URL.find(([pattern]) => pattern.test(publicUrl))?.[1];
  if (!source) return null;
  return `https://firms.modaps.eosdis.nasa.gov/api/area/csv/${encodeURIComponent(MAP_KEY)}/${source}/${INDIA_BBOX}/${dayRangeFromPublicUrl(publicUrl)}`;
}

async function firmsAwareFetch(input, init) {
  const publicUrl = typeof input === 'string' ? input : input instanceof URL ? input.href : input?.url;
  const areaUrl = typeof publicUrl === 'string' ? areaApiUrlFor(publicUrl) : null;
  if (areaUrl) {
    try {
      const response = await nativeFetch(areaUrl, init);
      if (response.ok) return response;
      await response.body?.cancel().catch(() => {});
      console.warn(`NASA FIRMS Area API returned HTTP ${response.status}; falling back to public download.`);
    } catch (error) {
      console.warn(`NASA FIRMS Area API failed; falling back to public download: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  return nativeFetch(input, init);
}

const port = Number(process.env.PORT ?? 8787);
const host = process.env.HOST ?? '127.0.0.1';
if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('PORT must be a valid TCP port.');

const server = createServer({ fetchImpl: firmsAwareFetch });
server.listen(port, host, () => {
  console.log(`AGNITE app + NASA FIRMS API: http://${host}:${server.address().port}`);
  console.log(`NASA FIRMS source mode: ${MAP_KEY ? 'Area API with public-download fallback' : 'public downloads (NASA_FIRMS_MAP_KEY not configured)'}`);
});
