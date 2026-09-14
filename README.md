<p align="center">
  <img src="public/brand/agnite-logo.png" alt="AGNITE logo" width="190" />
</p>

<h1 align="center">AGNITE — AI-Powered Thermal Intelligence</h1>

<p align="center"><strong>Detect • Understand • Predict • Explain • Act</strong></p>

[![AGNITE CI](https://github.com/goyalparth61-netizen/Agnite/actions/workflows/ci.yml/badge.svg)](https://github.com/goyalparth61-netizen/Agnite/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![React](https://img.shields.io/badge/React-TypeScript-blue)](package.json)
[![NASA FIRMS](https://img.shields.io/badge/Data-NASA%20FIRMS-orange)](https://firms.modaps.eosdis.nasa.gov/)

**AGNITE** is an India-focused thermal-intelligence platform built by **Team Timepass, Quantum University** for **Smart India Hackathon 2026 — SIH26162**.

It goes beyond plotting thermal hotspots by connecting each selected location with its **history, thermal baseline, nearby industrial/geographic context, explainable classification, future recurrence/risk windows, grounded AI explanation, monitoring and reporting**.

> **Core idea:** Past → Present → Understand → Predict → Explain → Act.

---

## Why AGNITE

Satellite thermal products are useful for locating heat anomalies, but a single hotspot does not answer the questions a user actually cares about:

- Has this location shown repeated thermal activity before?
- Is the current FRP significantly different from its historical baseline?
- Is the pattern more consistent with industrial heat, a natural/forest event or another anomaly?
- What evidence supports that conclusion?
- What may happen in the next 24h, 48h or 7d?
- What context or evidence is still missing?

AGNITE turns those questions into one map-centric decision-support workflow.

---

## Key capabilities

### Live thermal workspace

- NASA FIRMS near-real-time feeds
- VIIRS NOAA-20, VIIRS Suomi NPP and MODIS
- 24h, 48h and 7d windows
- India-region interactive map
- FRP filtering, sorting and CSV export
- stale-cache and upstream-error handling without fake replacement data

### Historical intelligence

- previous detections within the selected site radius
- pass-level FRP history
- baseline FRP
- anomaly/change from baseline
- trend, recurrence and persistence indicators
- saved-report history

### Explainable thermal classification

AGNITE evaluates four candidate thermal patterns:

- Industrial Fire
- Persistent Industrial Heat
- Forest / Natural Fire
- Other Thermal Anomaly

The classifier is designed to **abstain** when evidence is insufficient or ambiguous instead of forcing a confident label.

### Spatial and geographic context

Nearby OpenStreetMap/Overpass evidence can surface:

- industrial land use
- power facilities
- works/kilns/chimneys
- forests and natural features
- mapped distance to nearby context

Mapped proximity is evidence for review, not proof of causality or site containment.

### Future risk / recurrence

AGNITE presents 24h, 48h and 7d windows.

Two modes exist:

1. **Heuristic simulation** — transparent screening index used when no trained historical recurrence artifact is available.
2. **Historical recurrence model** — activated only when `src/ai/recurrence-model.json` contains a successfully trained real-data artifact.

The recurrence task estimates another FIRMS thermal detection in the same spatial cell; it is **not the same as predicting a confirmed fire incident**.

### AGNITE AI

AGNITE AI is grounded in the selected hotspot and its evidence.

It can explain:

- why a site was classified a certain way;
- what changed compared with history;
- what the current risk/recurrence window means;
- what evidence is missing;
- what precautions or next verification steps are appropriate.

A server-side OpenAI-compatible provider can be configured, with local grounded fallback retained.

### Monitoring and alerts

- save monitored locations in-browser
- compare new loaded FIRMS observations against thresholds
- export reports and alert graphics
- optional email subscriptions with explicit consent and email confirmation
- unsubscribe/delete flow

---

## Architecture

```text
User
  ↓
React / Vite / TypeScript
  ↓
Interactive India Map
  ↓
NASA FIRMS + OpenStreetMap Context
  ↓
Observation Validation / Spatial Filtering
  ↓
Historical Intelligence
  ↓
Classification + Conservative Abstention
  ↓
24h / 48h / 7d Risk or Recurrence
  ↓
AGNITE AI
  ↓
Reports / Alerts / Safety Guidance
```

Detailed design: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| UI / motion | Framer Motion, Lucide React |
| Maps | Leaflet, OpenStreetMap |
| Charts | Recharts |
| Backend | Node.js ESM HTTP server |
| Satellite data | NASA FIRMS |
| Spatial context | OpenStreetMap / Overpass |
| ML runtime | TypeScript/browser inference + JSON artifacts |
| ML training | Python scripts |
| AI assistant | Local grounding + optional OpenAI-compatible provider |
| Alerts | In-browser monitoring + optional Resend email workflow |
| Deployment | Render-compatible single service |
| CI | GitHub Actions |

---

## Quick start

### Requirements

- Node.js 22+
- npm

### Development

```sh
git clone https://github.com/goyalparth61-netizen/Agnite.git
cd Agnite
npm ci
npm run dev
```

Development starts:

- API: `http://127.0.0.1:8787`
- Vite UI: normally `http://localhost:5173`

Open:

```text
http://localhost:5173/#/workspace
```

### Production build

```sh
npm test
npm run build
npm start
```

Then open:

```text
http://127.0.0.1:8787/#/workspace
```

---

## Environment configuration

Use `.env.example` as the reference. Never commit real keys.

Optional integrations include:

- `AGNITE_LLM_API_KEY`
- `AGNITE_LLM_BASE_URL`
- `AGNITE_LLM_MODEL`
- `AGNITE_EMAIL_API_KEY`
- `AGNITE_EMAIL_FROM`
- `AGNITE_PUBLIC_URL`
- `AGNITE_CONTACT_EMAIL`
- `AGNITE_ALERT_STORE`
- `NASA_FIRMS_MAP_KEY` for offline historical training-data downloads

Configuration guides:

- [AGNITE AI](server/AI-CONFIG.md)
- [Email alerts](server/ALERTS-CONFIG.md)
- [Deployment](docs/DEPLOYMENT.md)

---

## API overview

Core routes:

```text
GET  /api/health
GET  /api/firms?sensor=noaa20&hours=24
GET  /api/site-context?latitude=...&longitude=...
POST /api/agnite/ask
GET  /api/alerts/status
POST /api/alerts/subscribe
POST /api/alerts/confirm
POST /api/alerts/unsubscribe
POST /api/contact
```

Full reference: [docs/API.md](docs/API.md)

---

## ML and prediction status

### Thermal classifier

The bundled classifier is trained on seeded **synthetic archetypes**. It demonstrates classification, explainability and conservative abstention.

It is **not a field-validated real-world fire classifier**.

The latest classifier gate is intentionally selective: ambiguous cases are withheld to increase precision on accepted synthetic cases. Any high precision reported from this artifact must be described specifically as **synthetic selective-validation precision**, not general fire-prediction accuracy.

### Historical recurrence model

The repository contains a reproducible path for real NASA FIRMS historical modelling:

```text
scripts/download-firms-history.py
scripts/train-firms-recurrence-model.py
ml/requirements.txt
src/ai/recurrence-model.json
```

The committed recurrence artifact currently starts with:

```json
{
  "trained": false
}
```

Until real historical training is completed, AGNITE automatically uses the heuristic risk simulation.

The real-data training pipeline targets **99% precision** for conservative positive decisions on chronological held-out recurrence labels. AGNITE does **not** assume that target is achieved in advance and does **not** describe it as 99% real-world fire-prediction accuracy.

Read: [docs/ML_PIPELINE.md](docs/ML_PIPELINE.md)

---

## Historical model training

Install the optional Python requirements:

```powershell
python -m pip install -r ml/requirements.txt
```

Set your NASA FIRMS MAP_KEY locally:

```powershell
$env:NASA_FIRMS_MAP_KEY="<your key>"
```

Download historical data:

```powershell
python scripts/download-firms-history.py `
  --start 2024-01-01 `
  --end 2026-08-31 `
  --source VIIRS_NOAA20_SP
```

Train:

```powershell
$files = Get-ChildItem "data\firms\*.csv" | Select-Object -ExpandProperty FullName
python scripts/train-firms-recurrence-model.py @files
```

Commit the generated artifact only after reviewing its held-out metrics.

---

## Data integrity and limitations

AGNITE deliberately distinguishes:

- **NASA DATA**
- **IMPORTED DATA**
- **MANUAL DATA**
- **SIMULATED DATA**

Important limitations:

- a satellite thermal detection is not automatically a confirmed fire;
- satellite passes are not continuous surveillance;
- OpenStreetMap centre-point distance does not establish facility containment;
- imported/manual data are not independently verified;
- demo observations are synthetic;
- the bundled classifier is synthetic-trained;
- the fallback future-risk score is a heuristic simulation;
- recurrence prediction is not the same target as confirmed-fire prediction.

Read: [docs/DATA_AND_LIMITATIONS.md](docs/DATA_AND_LIMITATIONS.md)

---

## Testing and CI

Run the core verification suite:

```sh
npm test
npm run build
```

Additional data/map verification utilities are available under `scripts/verify-*.mjs`.

GitHub Actions runs tests and the production build on repository updates.

---

## Deployment

A `render.yaml` blueprint is included.

Production model:

```text
One Node service
├── serves dist/
├── serves /api/*
└── keeps provider secrets server-side
```

Deployment instructions: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## Documentation

| Guide | Link |
| --- | --- |
| Documentation index | [docs/README.md](docs/README.md) |
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| API reference | [docs/API.md](docs/API.md) |
| ML pipeline | [docs/ML_PIPELINE.md](docs/ML_PIPELINE.md) |
| Data & limitations | [docs/DATA_AND_LIMITATIONS.md](docs/DATA_AND_LIMITATIONS.md) |
| Deployment | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| Demo / judging guide | [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md) |
| Project structure | [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) |
| Roadmap | [docs/ROADMAP.md](docs/ROADMAP.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Security | [SECURITY.md](SECURITY.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) |

---

## Team Timepass

**Quantum University — Smart India Hackathon 2026**

| Member | Program |
| --- | --- |
| Archi Sharma | B.Tech AI/ML |
| Parth Goyal | B.Tech CSCQ |
| Sonu Sharma | B.Tech CSCQ |
| Nandani Gautam | BCA |
| Dipanshu Jasrotia | B.Tech CSCQ |
| Dipanshu Negi | B.Tech CSE |

---

## Responsible-use statement

AGNITE is a **decision-support prototype**, not an emergency-response authority.

For real incidents, users should rely on official alerts, emergency services, field verification and qualified safety procedures.

---

## License

Application code is released under the [MIT License](LICENSE).

External datasets and map layers retain their own attribution/licensing terms. See `public/data/README.md`, `public/data/MAP-SOURCES.md` and the documentation above.
