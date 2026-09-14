# AGNITE System Architecture

## Purpose

AGNITE is an India-focused thermal-intelligence application that combines satellite detections, local/historical evidence, mapped context, explainable analysis, risk/recurrence windows and a grounded assistant.

The application is designed around the sequence:

**Detect → contextualize → compare with history → classify/abstain → estimate recurrence/risk → explain → monitor.**

## High-level architecture

```text
                         ┌──────────────────────────┐
                         │        User / Judge      │
                         └────────────┬─────────────┘
                                      │
                                      v
                     ┌────────────────────────────────┐
                     │ React + Vite + TypeScript UI   │
                     │ Home / India Map / Workspace   │
                     └───────┬─────────┬──────────────┘
                             │         │
               /api/firms    │         │ /api/site-context
                             v         v
                  ┌──────────────┐  ┌──────────────────┐
                  │ NASA FIRMS   │  │ OSM / Overpass   │
                  │ NRT thermal  │  │ mapped context   │
                  └──────┬───────┘  └────────┬─────────┘
                         │                   │
                         └──────────┬────────┘
                                    v
                    ┌──────────────────────────────┐
                    │ Observation validation       │
                    │ provenance + spatial filter  │
                    │ time window + de-duplication │
                    └──────────────┬───────────────┘
                                   v
                  ┌──────────────────────────────────┐
                  │ Historical intelligence          │
                  │ FRP baseline / trend / recurrence│
                  │ persistence / nearby observations│
                  └──────────────┬───────────────────┘
                                 │
                  ┌──────────────┴──────────────┐
                  v                             v
       ┌─────────────────────────┐  ┌────────────────────────┐
       │ Thermal classifier      │  │ Future-risk layer      │
       │ + conservative abstain  │  │ heuristic OR trained   │
       │ explainable features    │  │ recurrence artifact    │
       └────────────┬────────────┘  └───────────┬────────────┘
                    └───────────────┬────────────┘
                                    v
                         ┌──────────────────────┐
                         │ AGNITE AI            │
                         │ evidence-grounded    │
                         │ local/provider mode  │
                         └──────────┬───────────┘
                                    v
                    ┌──────────────────────────────┐
                    │ Reports / Alerts / Guidance  │
                    │ CSV/JSON export / monitoring │
                    └──────────────────────────────┘
```

## Frontend

The frontend is a React/Vite single-page application using hash navigation. Major surfaces are:

- **Home:** product narrative, India place discovery, documentation, awareness and team sections.
- **Workspace / Feed:** NASA observations, map exploration, filtering and site selection.
- **AGNITE AI / Analysis:** site context, classifier output, evidence, contributions and thermal history.
- **Risk:** 24h, 48h and 7d windows. The interface distinguishes heuristic simulation from a trained recurrence model.
- **Alerts:** in-browser watches and optional confirmed email subscriptions.
- **Saved reports / Import / Assistant:** persistence, local CSV workflows and evidence-grounded Q&A.

Key frontend modules live under `src/pages`, `src/components`, `src/hooks`, `src/ai` and `src/styles`.

## Backend

The production backend is a lightweight Node.js HTTP server in `server/index.mjs`.

Responsibilities:

- retrieve and normalize fixed NASA FIRMS public feeds;
- enforce query allowlists, response size limits and timeouts;
- cache successful FIRMS responses for ten minutes;
- return stale cache explicitly when upstream retrieval fails;
- serve OpenStreetMap/Overpass context through a bounded proxy;
- handle AGNITE AI provider requests;
- manage optional confirmed email alerts and contact delivery;
- serve the compiled frontend from `dist/` in production.

## Intelligence layer

### Classification

`src/ai/thermalEngine.ts` validates observations, builds a local temporal/spatial feature vector and applies the bundled multinomial classifier. The engine can abstain when history, context, input range or class separation is insufficient.

The bundled classifier artifact is synthetic-trained and must not be represented as field-validated.

### Historical intelligence

`src/ai/intelligence.ts` summarizes observations around a selected site, including:

- previous detections;
- distinct passes;
- FRP baseline and anomaly;
- trend;
- recurrence/persistence indicators;
- contextual factors and missing evidence.

### Recurrence model

`src/ai/recurrenceModel.ts` is the inference adapter for a separately trained NASA FIRMS historical recurrence artifact in `src/ai/recurrence-model.json`.

If the artifact is not trained, AGNITE falls back to a transparent heuristic simulation. The placeholder artifact currently reports `trained: false`; this prevents the UI from presenting an untrained model as real prediction.

## Data flow and provenance

Each observation carries a source category such as `firms`, `imported`, `manual` or `demo`. AGNITE deliberately keeps simulated and non-simulated histories separate.

NASA FIRMS data is never replaced with demo data after a network failure. The server either returns real fresh data, explicitly stale cached data, or an error.

## Reliability controls

The architecture includes:

- strict coordinate, date and numeric validation;
- duplicate removal;
- spatial filtering around selected locations;
- bounded request and response sizes;
- fixed upstream NASA URLs;
- timeouts and in-memory cache;
- static path traversal protection;
- model abstention;
- source labels and model limitations in the UI;
- deterministic fixture-based tests;
- CI running tests and production build on pushes.

## Deployment topology

The preferred production topology is one Node service:

```text
Internet
   │
   v
Render / Node service
   ├── serves dist/ frontend
   ├── /api/firms
   ├── /api/site-context
   ├── /api/agnite/ask
   ├── /api/alerts/*
   └── /api/contact
```

This avoids cross-origin complexity and keeps provider keys server-side.
