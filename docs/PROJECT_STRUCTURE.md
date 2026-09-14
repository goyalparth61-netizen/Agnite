# Project Structure

```text
Agnite/
├── .github/
│   └── workflows/              # CI automation
├── docs/                       # Technical and operational documentation
├── ml/                         # Python ML requirements/support files
├── public/
│   └── data/                   # Static geographic/directory datasets + provenance
├── scripts/                    # Dev, verification, import and ML training utilities
├── server/                     # Node backend and integrations
├── src/
│   ├── ai/                     # Analysis, intelligence, recurrence, assistant and storage logic
│   ├── components/             # Reusable UI grouped by product area
│   ├── data/                   # Frontend data/configuration
│   ├── hooks/                  # React data hooks
│   ├── pages/                  # Top-level Home and Workspace screens
│   └── styles/                 # Shared and workspace styling
├── .env.example                # Environment variable template
├── package.json                # Node scripts/dependencies
├── render.yaml                 # Render deployment definition
├── tsconfig.json               # Frontend TypeScript config
└── vite.config.ts              # Vite dev/build configuration
```

## Key modules

### `server/index.mjs`

Core production HTTP service:

- NASA FIRMS retrieval and normalization;
- validation, cache and stale fallback;
- `/api/health`;
- `/api/firms`;
- `/api/site-context`;
- frontend static serving.

### `server/aiProvider.mjs`

Optional OpenAI-compatible AGNITE AI provider integration. Provider secrets stay server-side.

### `server/notifications.mjs`

Optional contact and confirmed email-alert service, including persistence, rate limiting, confirmation/unsubscribe flow and periodic NASA checks.

### `server/siteContext.mjs`

Bounded OpenStreetMap/Overpass lookup for nearby industrial/geographic evidence.

### `src/ai/thermalEngine.ts`

Observation validation, classification, abstention, evidence and heuristic screening logic.

### `src/ai/model.json`

Bundled synthetic classifier artifact. Do not treat it as a real-world validated fire model.

### `src/ai/intelligence.ts`

Selected-site history, baseline, trend, recurrence/persistence summary and choice between learned recurrence inference vs heuristic fallback.

### `src/ai/recurrenceModel.ts`

Runtime adapter for the historical recurrence artifact.

### `src/ai/recurrence-model.json`

Historical recurrence artifact placeholder/trained output. The placeholder has `trained: false` until the offline training pipeline generates a model.

### `src/ai/assistantService.ts` / local assistant modules

Grounded assistant path for explaining selected evidence, with optional provider mode.

### `src/pages/Workspace.tsx`

Mission-control screen coordinating feed, analysis, risk, monitoring, history, import and assistant tabs.

### `src/components/workspace/ObservationMap.tsx`

Interactive observation map and selection flow.

### `src/components/workspace/AnalysisPanel.tsx`

Site context input, classifier results, evidence, history chart, feature contributions and limitations.

### `src/components/risk/RiskOverview.tsx`

24h/48h/7d risk or recurrence presentation.

## Scripts

Important scripts include:

- `scripts/dev.mjs` — combined backend + frontend development runner;
- `scripts/train-thermal-model.py` — reproducible synthetic classifier experiment;
- `scripts/download-firms-history.py` — historical NASA FIRMS downloader using a MAP_KEY;
- `scripts/train-firms-recurrence-model.py` — real historical recurrence training path;
- `scripts/import-india-places.py` — geographic directory refresh;
- `scripts/verify-*.mjs` — deterministic verification suites.

## Where to make changes

| Change | Primary location |
| --- | --- |
| NASA parsing/feed behaviour | `server/index.mjs` + FIRMS verification script |
| AI provider | `server/aiProvider.mjs`, `server/AI-CONFIG.md` |
| Email alerts | `server/notifications.mjs`, `server/ALERTS-CONFIG.md` |
| Classification | `src/ai/thermalEngine.ts`, model artifact, engine tests |
| Recurrence prediction | `src/ai/recurrenceModel.ts`, training script, artifact |
| Risk UI | `src/components/risk/` |
| Workspace UX | `src/pages/Workspace.tsx`, `src/components/workspace/` |
| Homepage | `src/pages/Home.tsx`, `src/components/home/` |
| Maps/geographic directory | `src/data/`, `public/data/`, map components |
| Documentation | `README.md`, `docs/`, `server/*-CONFIG.md` |

## Change discipline

When changing a data or model contract, update all three layers together:

1. producer/parser;
2. consuming TypeScript/UI code;
3. deterministic verification/documentation.

This prevents the repository from accumulating undocumented behaviour or stale interfaces.
