<p align="center">
  <img src="https://raw.githubusercontent.com/goyalparth61-netizen/Agnite/main/public/brand/agnite-logo.png" alt="AGNITE logo" width="260" />
</p>

<h1 align="center">AGNITE</h1>

<p align="center">
  <strong>AI-Powered Thermal Intelligence for India</strong>
</p>

<p align="center">
  Detect • Understand • Classify • Predict • Explain • Act
</p>

<p align="center">
  <a href="https://github.com/goyalparth61-netizen/Agnite/actions/workflows/ci.yml"><img src="https://github.com/goyalparth61-netizen/Agnite/actions/workflows/ci.yml/badge.svg" alt="AGNITE CI" /></a>
  <img src="https://img.shields.io/badge/React-TypeScript-3178C6?logo=react&logoColor=white" alt="React TypeScript" />
  <img src="https://img.shields.io/badge/Data-NASA%20FIRMS-F57C00" alt="NASA FIRMS" />
  <img src="https://img.shields.io/badge/Maps-Leaflet%20%2B%20OSM-199900" alt="Leaflet OpenStreetMap" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-2ea44f" alt="MIT License" /></a>
</p>

<p align="center">
  <strong>Team Timepass · Quantum University · Smart India Hackathon 2026 · SIH26162</strong>
</p>

---

## Overview

**AGNITE** is an India-focused AI and GIS platform for understanding thermal activity detected from space.

The core problem statement is:

> **AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources Using NASA FIRMS.**

Instead of showing a thermal hotspot as a single dot on a map, AGNITE builds context around that location. It combines current satellite observations, previous detections, thermal behaviour, nearby industrial/geographic evidence, explainable classification, future risk/recurrence windows, alerts and a grounded AI assistant.

The product is designed around one simple story:

```text
PAST → PRESENT → UNDERSTAND → CLASSIFY → PREDICT → EXPLAIN → ACT
```

A person should be able to open AGNITE, select a location in India and understand:

- what thermal activity is visible now;
- what happened at the same location previously;
- whether the pattern looks persistent or abnormal;
- whether nearby industrial or geographic context may matter;
- which thermal class best fits the available evidence;
- what the next 24h / 48h / 7d risk or recurrence window looks like;
- why AGNITE reached that result;
- what evidence is missing;
- what precautions or monitoring actions may be appropriate.

> [!IMPORTANT]
> AGNITE is a decision-support prototype. A satellite thermal detection is **not automatically a confirmed fire**, and the platform is not an emergency-response authority.

---

## What makes AGNITE different

Most hotspot viewers answer **where** thermal activity was detected.

AGNITE is being built to answer the next questions:

| Question | AGNITE capability |
| --- | --- |
| Where is thermal activity occurring? | Interactive India-focused map using NASA FIRMS observations |
| Has this location behaved like this before? | Historical detections, baseline FRP, trend and recurrence analysis |
| Is this likely persistent heat or an abnormal event? | Explainable multi-class thermal classification with abstention |
| Is an industry or geographic feature nearby? | OpenStreetMap / Overpass spatial context |
| What may happen next? | 24h / 48h / 7d risk or thermal-recurrence windows |
| Why did the system produce this result? | Evidence, feature contributions and AGNITE AI explanations |
| Can I monitor this location? | Saved locations, thresholds, reports and optional email alerts |
| What should I do next? | Safety guidance, missing-evidence checks and recommended verification steps |

---

## Core platform capabilities

### 1. Interactive India thermal map

The workspace can load near-real-time NASA FIRMS observations and display them on an interactive Leaflet map.

Supported feeds include:

- VIIRS NOAA-20
- VIIRS Suomi NPP
- MODIS Terra/Aqua
- 24-hour, 48-hour and 7-day windows

Users can inspect detections, filter by FRP, sort results, search coordinates, select a hotspot and export filtered observations.

The backend currently filters a South Asia public feed to an India-region bounding box. This improves usability but is **not an exact political-boundary filter**.

### 2. Historical thermal intelligence

For a selected site, AGNITE can derive:

- previous nearby detections;
- current FRP;
- historical baseline FRP;
- percentage deviation from baseline;
- recent thermal trend;
- repeated satellite passes;
- recurrence indicators;
- observed-day persistence;
- saved-report history.

This gives the AI and classification layers temporal context instead of treating every hotspot independently.

### 3. Explainable thermal classification

AGNITE currently evaluates four thermal patterns:

- **Industrial Fire**
- **Persistent Industrial Heat**
- **Forest / Natural Fire**
- **Other Thermal Anomaly**

The classifier uses thermal, spatial and temporal evidence and is intentionally designed to **abstain** when evidence is weak or ambiguous.

An abstention is better than a confident but unsupported label.

### 4. Persistent heat handling

Industrial facilities may repeatedly generate legitimate heat through furnaces, kilns, power generation, process heat or other operations.

AGNITE therefore considers recurrence, historical baseline and nearby mapped industrial context before treating a repeated thermal signal as an abnormal event.

Mapped proximity alone does not prove that a hotspot belongs to a facility or identify the source of heat.

### 5. Spatial context

`/api/site-context` queries OpenStreetMap / Overpass for mapped features near a selected point, including relevant industrial and geographic context.

Examples include:

- industrial land use;
- power facilities;
- works, kilns and chimneys;
- forests and woodland;
- residential areas;
- water and scrub.

These features are supporting evidence, not verified causality.

### 6. Future risk / recurrence windows

AGNITE presents:

- **24h**
- **48h**
- **7d**

Two prediction modes are supported by the architecture:

**Heuristic simulation**  
Used while a validated historical recurrence model is unavailable. The score is transparent and based on displayed factors such as FRP, baseline deviation, recurrence, trend and supplied context.

**Historical thermal-recurrence model**  
A reproducible Python pipeline can train 24h / 48h / 7d recurrence models from historical NASA FIRMS CSV data. The trained artifact is activated only after it exists and has been reviewed.

The prediction target is another thermal detection in the same spatial cell. It is **not equivalent to predicting a confirmed fire incident**.

### 7. AGNITE AI

AGNITE AI is designed as a **grounded thermal-intelligence assistant**, not a generic chatbot.

It receives structured evidence from the selected site and can answer questions such as:

- Why is this hotspot risky?
- What changed from the historical baseline?
- Is this pattern more consistent with persistent industrial heat or an abnormal fire-like event?
- What happened at this location previously?
- What could the next 24h / 48h / 7d window mean?
- Which evidence is missing?
- What precautions or verification steps should be considered?
- What are FRP, VIIRS, MODIS and NASA FIRMS?

The application supports a server-side OpenAI-compatible provider and retains a local evidence-grounded fallback.

### 8. Risk visualization

Risk is presented with clear levels and visual states:

```text
LOW       → Green
MODERATE  → Yellow
HIGH      → Orange
CRITICAL  → Red
```

The interface also shows contributing factors and missing evidence so that a score is not presented as an unexplained number.

### 9. Monitoring and alerts

Users can:

- save monitored coordinates;
- define FRP thresholds;
- compare nearby loaded NASA observations;
- export reports;
- generate alert graphics;
- optionally subscribe to email notifications.

Email subscriptions require explicit consent and confirmation. Demo, manual and imported observations do not trigger production email alerts.

### 10. Awareness and safety

The platform includes educational fire/thermal-awareness content, safety guidance and links to official public resources. This layer is intended to make the platform understandable to non-technical users as well as technical evaluators.

---

## System architecture

```text
                         ┌──────────────────────┐
                         │        USER          │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │  REACT / TYPESCRIPT  │
                         │  Multi-page UI + GIS │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │      INTERACTIVE INDIA MAP     │
                    └───────────────┬────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
      ┌───────▼────────┐   ┌────────▼────────┐   ┌───────▼────────┐
      │   NASA FIRMS   │   │ OSM / OVERPASS │   │ USER / IMPORT  │
      │ Thermal signal │   │ Spatial context│   │ Optional data  │
      └───────┬────────┘   └────────┬────────┘   └───────┬────────┘
              └─────────────────────┼─────────────────────┘
                                    │
                         ┌──────────▼───────────┐
                         │ OBSERVATION PIPELINE │
                         │ validate • filter    │
                         │ dedupe • normalize   │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │ HISTORICAL ANALYSIS  │
                         │ baseline • trend     │
                         │ recurrence • persist │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼──────────────────────┐
              │                     │                      │
     ┌────────▼─────────┐  ┌────────▼─────────┐  ┌────────▼────────┐
     │ CLASSIFICATION   │  │ RISK / RECURRENCE│  │  EXPLAINABILITY │
     │ + ABSTENTION     │  │ 24h • 48h • 7d   │  │ factors/evidence│
     └────────┬─────────┘  └────────┬─────────┘  └────────┬────────┘
              └─────────────────────┼──────────────────────┘
                                    │
                         ┌──────────▼───────────┐
                         │      AGNITE AI       │
                         │ grounded explanation │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
       ┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
       │    RISK     │      │   ALERTS    │      │   REPORTS   │
       └─────────────┘      └─────────────┘      └─────────────┘
```

For the full technical breakdown, see **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

---

## Data flow

```text
NASA FIRMS
    ↓
Hotspot selected
    ↓
Spatial + Thermal + Temporal features
    ↓
Historical baseline and recurrence analysis
    ↓
Explainable classification
    ↓
Industrial Fire / Persistent Industrial Heat /
Forest-Natural Fire / Other / Insufficient Evidence
    ↓
24h / 48h / 7d risk or recurrence layer
    ↓
AGNITE AI
    ↓
Risk • explanation • precautions • monitoring • alerts
```

---

## Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| Animation | Framer Motion |
| Mapping | Leaflet, OpenStreetMap |
| Charts | Recharts |
| Icons | Lucide React |
| Backend | Node.js ESM HTTP server |
| Satellite data | NASA FIRMS |
| Spatial context | OpenStreetMap / Overpass |
| ML runtime | TypeScript inference + JSON model artifacts |
| ML training | Python |
| AI assistant | Grounded local assistant + optional OpenAI-compatible provider |
| Email alerts | Resend-compatible workflow |
| Deployment | Render-compatible single web service |
| CI | GitHub Actions |

---

## Current MVP status

| Component | Status | Notes |
| --- | --- | --- |
| Multi-page product UI | ✅ Ready | Home, Platform, Intelligence, Risk, Learn, About, Workspace |
| India-focused interactive GIS | ✅ Ready | Leaflet + NASA observations |
| NASA FIRMS feed integration | ✅ Ready | NOAA-20, SNPP, MODIS |
| Historical intelligence | ✅ Ready | Based on loaded observations / saved reports |
| OSM industrial/geographic context | ✅ Ready | Supporting mapped evidence |
| Thermal classification | 🧪 Experimental | Synthetic-trained classifier with conservative abstention |
| Persistent-heat analysis | ✅ MVP ready | Uses recurrence, baseline and spatial context |
| Risk visualization | ✅ Ready | 24h / 48h / 7d display |
| Historical recurrence pipeline | 🧪 Training-ready | Real-data artifact not yet committed |
| AGNITE AI local mode | ✅ Ready | Evidence-grounded fallback |
| External conversational AI | ⚙️ Configurable | Requires server-side LLM API key |
| In-app monitoring | ✅ Ready | Saved sites and thresholds |
| Email alerts | ⚙️ Configurable | Requires email provider configuration |
| Reports / exports | ✅ Ready | JSON/CSV/SVG workflows |
| CI / production build | ✅ Ready | GitHub Actions |
| Render deployment config | ✅ Ready | `render.yaml` included |

---

## Model and prediction integrity

### Thermal classifier

The currently bundled classifier is an **experimental synthetic-trained model** used to demonstrate the classification and explainability pipeline.

It does **not** establish real-world industrial-fire accuracy.

The engine uses conservative acceptance logic and can return:

```text
Insufficient evidence
```

instead of forcing a label.

### About the 99% target

The historical recurrence training pipeline can search for a decision threshold targeting **99% precision on chronological held-out data**.

That target is not assumed to be achieved.

AGNITE does **not** claim:

- 99% real-world fire prediction accuracy;
- guaranteed fire occurrence;
- an exact future incident date;
- NASA-confirmed incident cause.

A 99% figure should be reported only if an actual held-out evaluation supports it, and then only with the exact metric and task description.

### Historical recurrence artifact

The committed artifact currently begins as:

```json
{
  "trained": false
}
```

When a reviewed real-data artifact is generated, the application can switch from the fallback heuristic layer to the trained recurrence model.

See **[docs/ML_PIPELINE.md](docs/ML_PIPELINE.md)**.

---

## Getting started

### Prerequisites

- Node.js **22+**
- npm
- Internet access for NASA FIRMS and map/context providers
- Python only if you want to train the historical recurrence model

### Clone and install

```bash
git clone https://github.com/goyalparth61-netizen/Agnite.git
cd Agnite
npm ci
```

### Development

```bash
npm run dev
```

This starts:

```text
Frontend: http://localhost:5173
Backend:  http://127.0.0.1:8787
```

Open the product:

```text
http://localhost:5173/
```

Open the thermal intelligence workspace directly:

```text
http://localhost:5173/#/workspace
```

### Verify before deployment

```bash
npm test
npm run build
```

### Production mode

```bash
npm start
```

The Node server serves both the built frontend and `/api/*` routes.

---

## Available scripts

| Command | Purpose |
| --- | --- |
| `npm run dev` | Starts frontend and backend development processes |
| `npm run dev:ui` | Starts Vite UI only |
| `npm run api` | Starts backend API only |
| `npm test` | Runs FIRMS, ML engine, import, intelligence, frontend and notification verification |
| `npm run build` | Type-checks and creates the production Vite build |
| `npm start` | Runs the production Node server |
| `npm run preview` | Previews the Vite build |

---

## Environment configuration

Copy `.env.example` as a reference and configure secrets only in your shell or deployment provider.

**Never commit real API keys.**

### AGNITE AI

```text
AGNITE_LLM_API_KEY=
AGNITE_LLM_BASE_URL=https://api.openai.com/v1
AGNITE_LLM_MODEL=gpt-4.1-mini
```

The provider is OpenAI-compatible, so a compatible gateway can also be used by changing the base URL and model identifier.

Detailed guide: **[server/AI-CONFIG.md](server/AI-CONFIG.md)**

### Email alerts

```text
AGNITE_EMAIL_API_KEY=
AGNITE_EMAIL_FROM=
AGNITE_PUBLIC_URL=
AGNITE_CONTACT_EMAIL=
AGNITE_ALERT_STORE=
```

Detailed guide: **[server/ALERTS-CONFIG.md](server/ALERTS-CONFIG.md)**

### Historical NASA training

```text
NASA_FIRMS_MAP_KEY=
```

This key is for the optional historical-data training workflow, not the existing public near-real-time feed used by the application.

---

## Historical recurrence training

Install Python requirements:

```powershell
python -m pip install -r ml/requirements.txt
```

Set the NASA FIRMS MAP_KEY locally:

```powershell
$env:NASA_FIRMS_MAP_KEY="YOUR_KEY"
```

Download historical data:

```powershell
python scripts/download-firms-history.py `
  --start 2024-01-01 `
  --end 2026-08-31 `
  --source VIIRS_NOAA20_SP
```

Train the recurrence models:

```powershell
$files = Get-ChildItem "data\firms\*.csv" | Select-Object -ExpandProperty FullName
python scripts/train-firms-recurrence-model.py @files
```

Review the generated metrics before committing `src/ai/recurrence-model.json`.

---

## API reference

Core application routes include:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Deployment health check |
| `GET` | `/api/firms?sensor=noaa20&hours=24` | NASA FIRMS thermal observations |
| `GET` | `/api/site-context?latitude=...&longitude=...` | Nearby mapped context |
| `POST` | `/api/agnite/ask` | Grounded AGNITE AI request |
| `GET` | `/api/alerts/status` | Alert-service availability |
| `POST` | `/api/alerts/subscribe` | Request alert subscription |
| `POST` | `/api/alerts/confirm` | Confirm subscription |
| `POST` | `/api/alerts/unsubscribe` | Remove subscription and stored data |
| `POST` | `/api/contact` | Contact workflow when email delivery is configured |

Full API documentation: **[docs/API.md](docs/API.md)**

---

## Data integrity

Every observation is kept distinguishable by provenance:

| Label | Meaning |
| --- | --- |
| `NASA DATA` | Loaded from the supported NASA FIRMS feed |
| `IMPORTED DATA` | User-imported observations |
| `MANUAL DATA` | User-entered observations |
| `SIMULATED DATA` | Explicit demo/test scenarios |

AGNITE does not silently replace unavailable NASA data with demo observations.

The application also validates inputs, removes duplicate measurements, bounds data volume and reports stale upstream data when cached observations are used.

Read **[docs/DATA_AND_LIMITATIONS.md](docs/DATA_AND_LIMITATIONS.md)** before making performance or operational claims.

---

## Project structure

```text
Agnite/
│
├── .github/
│   ├── ISSUE_TEMPLATE/          # structured issue templates
│   └── workflows/               # CI
│
├── docs/                        # engineering and judging documentation
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── DATA_AND_LIMITATIONS.md
│   ├── DEMO_GUIDE.md
│   ├── DEPLOYMENT.md
│   ├── ML_PIPELINE.md
│   ├── PROJECT_STRUCTURE.md
│   └── ROADMAP.md
│
├── ml/                          # Python ML requirements
├── public/
│   ├── brand/                   # AGNITE identity assets
│   └── data/                    # map/place datasets and attribution
│
├── scripts/                     # verification, import and training utilities
├── server/                      # Node backend, AI, alerts, site context
├── src/
│   ├── ai/                      # intelligence, classifier, model artifacts
│   ├── components/              # UI modules
│   ├── data/                    # product data
│   ├── hooks/                   # application hooks
│   ├── pages/                   # multi-page product routes
│   └── styles/                  # visual system
│
├── .env.example
├── render.yaml
├── package.json
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
└── README.md
```

Full map: **[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)**

---

## Documentation

| Document | Purpose |
| --- | --- |
| [Documentation Index](docs/README.md) | Entry point for technical docs |
| [Architecture](docs/ARCHITECTURE.md) | Full system and data-flow design |
| [API Reference](docs/API.md) | Backend endpoints and behaviour |
| [ML Pipeline](docs/ML_PIPELINE.md) | Classification and recurrence modelling |
| [Data & Limitations](docs/DATA_AND_LIMITATIONS.md) | Provenance, assumptions and claim boundaries |
| [Deployment](docs/DEPLOYMENT.md) | Production deployment checklist |
| [Demo Guide](docs/DEMO_GUIDE.md) | Suggested evaluator/judge walkthrough |
| [Project Structure](docs/PROJECT_STRUCTURE.md) | Repository layout |
| [Roadmap](docs/ROADMAP.md) | Future engineering priorities |
| [Contributing](CONTRIBUTING.md) | Contribution workflow |
| [Security](SECURITY.md) | Security reporting and secret handling |
| [Changelog](CHANGELOG.md) | Project evolution |

---

## Deployment

AGNITE is designed to run as a single production Node service:

```text
Render / Node Service
├── serves dist/
├── serves /api/*
├── keeps LLM/email secrets server-side
└── exposes /api/health
```

A Render blueprint is already included in `render.yaml`.

Recommended deployment flow:

```bash
npm ci
npm test
npm run build
npm start
```

Then verify:

```text
/api/health
Homepage
Dashboard
NASA feed
Hotspot selection
Site analysis
24h / 48h / 7d intelligence
AGNITE AI
Alerts / reports
```

Detailed deployment guide: **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**

---

## Recommended demo flow

For an evaluator or hackathon judge:

1. Open the **Home** page and explain the problem in one sentence.
2. Open **Dashboard**.
3. Load a NASA FIRMS feed.
4. Select a thermal detection on the India map.
5. Show current FRP and historical thermal behaviour.
6. Load nearby industrial/geographic context.
7. Run the classification engine.
8. Explain whether AGNITE classified the site or abstained.
9. Show 24h / 48h / 7d risk or recurrence windows.
10. Ask **AGNITE AI** why the system reached that result.
11. Show risk factors, missing evidence and precautions.
12. Demonstrate monitoring/report/alert capability.

Full walkthrough: **[docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md)**

---

## Team Timepass

**Quantum University · Smart India Hackathon 2026 · SIH26162**

| Member | Program |
| --- | --- |
| **Archi Sharma** | B.Tech AI/ML |
| **Parth Goyal** | B.Tech CSCQ |
| **Sonu Sharma** | B.Tech CSCQ |
| **Nandani Gautam** | BCA |
| **Dipanshu Jasrotia** | B.Tech CSCQ |
| **Dipanshu Negi** | B.Tech CSE |

---

## Roadmap

Key next engineering milestones include:

- larger multi-year historical NASA FIRMS training datasets;
- geographically held-out model evaluation;
- verified industrial/facility datasets;
- automated weather and wind integration;
- stronger field-incident labels for real-world classification validation;
- probability calibration and drift monitoring;
- production database for multi-instance alert infrastructure;
- richer live awareness/news sources;
- mobile-focused experience and notification workflows.

See **[docs/ROADMAP.md](docs/ROADMAP.md)**.

---

## Responsible use

AGNITE provides **thermal-intelligence decision support**.

It should not be used as the sole basis for emergency action, industrial shutdown decisions, evacuation orders or claims about the cause of a real-world fire.

For actual incidents, rely on official alerts, emergency services, field verification and qualified safety procedures.

---

## Contributing

Contributions, bug reports and feature proposals are welcome through the structured GitHub workflow.

Please read **[CONTRIBUTING.md](CONTRIBUTING.md)** before submitting changes.

Security-sensitive issues should follow **[SECURITY.md](SECURITY.md)** rather than being posted publicly.

---

## License and attribution

AGNITE application code is released under the **[MIT License](LICENSE)**.

External data and map layers retain their own terms and attribution requirements, including NASA FIRMS, OpenStreetMap, GeoNames and Natural Earth resources used by the project.

See:

- [public/data/README.md](public/data/README.md)
- [public/data/MAP-SOURCES.md](public/data/MAP-SOURCES.md)

---

<p align="center">
  <strong>AGNITE</strong><br/>
  From thermal signals to explainable intelligence.
</p>
