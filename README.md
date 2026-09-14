# AGNITE - Thermal Intelligence

React, Vite and TypeScript application with a Node.js NASA FIRMS service and an experimental local thermal classifier. Built by Team Timepass for Smart India Hackathon 2026, SIH26162.

The homepage contains the India place directory and labeled demonstration scenarios. The separate **AGNITE workspace** at `/#/workspace` loads real NASA satellite detections, analyzes supplied observations, imports CSV files, saves reports and monitors selected coordinates.

## Run locally

Use Node.js 24 and npm. No NASA API key, account or additional backend package is required for the public downloads used here.

```sh
npm install
npm run dev
```

`dev` starts the Node API on `http://127.0.0.1:8787` and Vite on the URL printed in the terminal, normally `http://localhost:5173`. Vite forwards `/api` requests to port 8787. Open the workspace from the homepage, or append `/#/workspace` to the Vite URL. Stop both processes with Ctrl+C.

For the production build:

```sh
npm run build
npm start
```

Open `http://127.0.0.1:8787/#/workspace`. This single Node process serves both `dist/` and the API. `HOST` and `PORT` can override its default `127.0.0.1:8787`; the Vite proxy is configured for port 8787.

`npm run preview` starts only Vite's build preview, normally on port 4173. To use the live workspace in preview, also run `npm run api` in another terminal. `npm run dev:ui` likewise needs the API started separately. Internet access is required for NASA downloads and OpenStreetMap tiles.

## Live NASA FIRMS feed

The workspace supports VIIRS NOAA-20 (the initial selection), VIIRS Suomi NPP and MODIS Terra/Aqua. Each sensor offers 24-hour, 48-hour and 7-day observation windows. Search coordinates or IDs, filter minimum fire radiative power (FRP, in MW), sort by acquisition time or FRP, select map/register detections and export filtered records as CSV.

The server retrieves fixed [NASA FIRMS public near-real-time downloads](https://firms.modaps.eosdis.nasa.gov/active_fire/) for South Asia, then applies **6-38 degrees north and 67-99 degrees east**. This is an India-region bounding box that **includes neighboring areas**, rather than an exact country boundary or city-level fire register. Source URLs, acquisition times and retrieval times remain visible. A thermal detection does not establish a fire's cause or count confirmed incidents.

```text
GET /api/firms?sensor=noaa20&hours=24
GET /api/health
```

Allowed sensors are `noaa20`, `snpp`, `modis`; allowed hours are `24`, `48`, `168`. The response contains `observations`, `fetchedAt`, `latestObservation`, `sourceUrl`, `sensor`, `windowHours`, `coverage`, `stale`, `cached` and optional `warning`. Each observation includes coordinates, UTC acquisition time, FRP and `source: "firms"`, with brightness and confidence when available.

Downloads have a 25-second timeout and 10 MB limit. CSV fields, calendar dates, coordinates and numeric ranges are validated; duplicates are removed and excluded rows are reported. Responses are capped at 50,000 observations. Concurrent requests for the same source share one download, and successful results are cached in memory for ten minutes. An upstream failure returns explicitly stale cached data with original timestamps, or HTTP 502 if no cache exists. Synthetic observations are never substituted for failed NASA downloads.

Auto-check runs every ten minutes while the workspace is open and the page is visible. Near-real-time data follows satellite acquisition and publication schedules; another check does not guarantee a new pass. The server cache is lost when its process restarts.

## AGNITE AI and local workflows

Select a detection and choose **Analyze site**. Analysis uses observations within 5 km, with the engine retaining up to 30 days of supplied history around the latest detection. Enter verified land cover, industrial distance and optional wind speed. These model inputs remain user verified. A nearby OpenStreetMap/Overpass panel now retrieves industrial and geographic features for review; feature-centre distance does not establish containment. Weather remains manual.

The bundled multinomial logistic regression is trained on **2,600 seeded synthetic examples**, with 800 separate synthetic validation examples. Training uses no real satellite or field labels. Inference runs in the browser. Candidate patterns are industrial fire, persistent industrial heat, forest/natural fire and other thermal anomaly; these experimental labels do not verify real causes.

Classification is withheld when evidence is inadequate: at least four distinct observation times spanning 48 hours, two baseline passes older than 24 hours, known land cover and industrial distance are required. The model also abstains for unsupported thermal ranges or ambiguous scores. Try a 7-day NASA window for more history. Relative model scores are **not calibrated confidence or fire probabilities**, and synthetic validation does not establish field accuracy.

Reports contain pass-level FRP history, a historical baseline, evidence, feature contributions when classification is available, and a transparent heuristic screening index. The 24-hour, 48-hour and 7-day ranges are **what-if scenarios**, not forecasts, statistical intervals or probabilities. Neither the classifier nor the index is validated for operational fire response.

- **Import data:** preview and validate UTF-8 CSV files up to 2 MB and 5,000 observations; inspect errors and duplicates before loading valid rows. Manual observations can build local history. Contents stay in the browser. Uploaded provenance becomes `imported`, while an explicit `demo` label remains simulated.
- **Saved reports:** retain up to 50 snapshots containing observations, context and analysis; inspect evidence, export JSON or delete reports. Browser `localStorage` holds the archive; clearing it removes saved items.
- **Monitoring:** save up to 50 named coordinates and FRP thresholds. Matches use the currently loaded NASA sensor/window within 5 km of each site. Saved-site matches are in-app monitoring. A separate confirmed email subscription can run on the server when configured; see `server/ALERTS-CONFIG.md`. These are satellite detection notices, not emergency notifications.
- **Ask AGNITE:** a local command assistant answers supported questions about loaded data, highest FRP, evidence, classification and monitoring. No conversational language model is connected.
- **Demo scenario:** explicitly loads simulated observations and context to explore the full analysis workflow independently of NASA availability.

CSV accepts `latitude`, `longitude`, `frp`, and either `observed_at` with an ISO timestamp including timezone or both NASA `acq_date` and `acq_time` (UTC HHMM). `id`, `brightness`/`bright_ti4` and `source` are optional. Example **synthetic** import:

```csv
latitude,longitude,observed_at,frp,source
21.1466,79.0889,2026-09-13T06:30:00Z,18,demo
```

Retrain the synthetic experiment with `python scripts/train-thermal-model.py`; it uses the Python standard library and writes the bundled model artifact.

## Homepage directory and maps

The bundled [GeoNames](https://www.geonames.org/) snapshot contains **549,021 populated-place records** across 36 named states/union territories, plus unspecified-region records. It includes cities, towns and villages and is not an exhaustive official city register. Names, coordinates, administrative assignments and source population records come from GeoNames; population is not a current estimate. Same-name places retain distinct GeoNames IDs, and alternate names are searchable.

The hero searches the complete directory and aggregates every record into selectable groups according to zoom and viewport. Its pan/zoom controls, selection and satellite sweep share one projection. The homepage demonstration dashboard uses Leaflet, grouped representative places, city focus and clearly synthetic hotspots, histories, classifications and risks. These directory demos remain separate from real NASA workspace observations; a directory entry does not imply a detected fire.

One shared Web Worker downloads, decompresses and searches the roughly 9.8 MB gzip dataset for the hero and dashboard. The Node server serves `.gz` as `application/gzip` without `Content-Encoding`; the worker detects gzip bytes and decompresses them, while also accepting already decoded responses from other hosts. OpenStreetMap provides street tiles. Natural Earth outlines are generalized geographic context, not legal boundaries. Solar background light, map sweeps and grid animations include pause/reduced-motion support.

Dataset provenance: [public/data/README.md](public/data/README.md). Homepage map attribution: [public/data/MAP-SOURCES.md](public/data/MAP-SOURCES.md). Refresh the directory with `python scripts/import-india-places.py` (network access required).

## Validation

```sh
npm test
npm run build
node scripts/verify-city-data.mjs
node scripts/verify-map-data.mjs
node scripts/verify-hero-map.mjs
node scripts/verify-shared-directory.mjs
```

`npm test` covers FIRMS parsing, source allowlists, caching, stale/error handling, download limits and static file containment, plus thermal analysis and CSV import/export. It uses deterministic fixtures rather than requiring NASA availability.

To check the compiled directory worker against preview:

```sh
npm run preview -- --host 127.0.0.1 --port 4173
# In another terminal:
node scripts/verify-city-worker.mjs
```

These scripts check data and application logic. Browser layout, keyboard interaction and complete workflows need browser checks; public NASA availability, tile availability and real-world model performance are not guaranteed by fixture tests.

## Code map

- `server/index.mjs`: HTTP server, NASA downloads, normalization, cache and production static serving.
- `scripts/dev.mjs`, `vite.config.ts`: combined development runner and API proxy.
- `src/pages/Workspace.tsx`, `src/components/workspace/`, `src/hooks/useFirmsFeed.ts`: workspace navigation, map/analysis interfaces and feed lifecycle.
- `src/ai/`: thermal engine, synthetic model, CSV import/export, local assistant and browser storage helpers.
- `src/pages/Home.tsx`, `src/components/home/`, `src/data/`: homepage, directory worker, map aggregation and demonstration data.
- `src/styles/`: shared design, maps and workspace layouts.

Application code is MIT licensed; [LICENSE](LICENSE) and `public/LICENSE` contain the license. GeoNames is CC BY 4.0 with separate attribution; Natural Earth geometry is public domain and OpenStreetMap attribution appears on maps.


## Added MVP workflows

- Click an arbitrary map location or enter coordinates to select the latest loaded detection within 5 km; empty areas are explicitly reported without inventing observations.
- Selected-hotspot classification initializes automatically. Existing model, dataset imports, archive, AI provider, layout and risk sections are retained.
- Nearby industry/geographic evidence is loaded from OpenStreetMap/Overpass, with source links and centre-distance limitations.
- Optional coordinate or browser-location email subscriptions use consent, email verification, periodic checks, persisted deduplication and unsubscribe/deletion. Configure the server using [ALERTS-CONFIG.md](server/ALERTS-CONFIG.md).
- Nearby detection cards can export an SVG alert image including acquisition time, source, FRP and index limitations.
- Contact enquiries use a configured team inbox; downloadable drafts work without delivery configuration.
- Awareness includes [official NDMA SACHET precautions and video resources](https://sachet.ndma.gov.in/DosDont) and links to official alerts.

The classifier is still synthetic-trained and future risk windows are heuristic scenarios, not validated occurrence probabilities. Verified incident labels, longer historical data and time/location-held-out evaluation are needed before claiming operational predictive accuracy. Automatic facility-boundary verification, live news ingestion and weather forecasts are not included.
