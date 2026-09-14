# AGNITE Roadmap

## Current foundation

Implemented and repository-backed capabilities:

- India-focused interactive thermal workspace;
- NASA FIRMS VIIRS/MODIS live feed handling;
- explicit source and stale-data states;
- hotspot selection and nearby history;
- FRP baseline, change, trend and recurrence summaries;
- synthetic-trained four-class thermal classifier;
- conservative insufficient-evidence abstention;
- OpenStreetMap/Overpass site context;
- 24h/48h/7d heuristic risk windows;
- historical NASA FIRMS recurrence-model training path;
- automatic runtime switch to a trained recurrence artifact when available;
- AGNITE AI local/provider modes;
- CSV import/export and saved reports;
- in-app watches and optional confirmed email alerts;
- production Node static/API service;
- Render deployment definition;
- deterministic CI tests and build validation.

## Priority 1 — Real historical validation

Goal: replace demonstration-only predictive claims with evidence-backed evaluation.

- collect multi-year NASA FIRMS history;
- train the recurrence artifact;
- evaluate later unseen dates;
- add geographic holdout tests;
- report precision, recall, coverage and threshold for every horizon;
- compare against simple persistence/baseline models;
- document failure modes and drift.

Success condition: real held-out metrics are reproducible and the UI reports exactly what was validated.

## Priority 2 — Stronger context data

- verified industrial facility datasets;
- reliable land-cover source;
- weather/wind observations and forecast data;
- terrain/fuel context where appropriate;
- boundary-aware facility distance instead of centre-point proximity.

## Priority 3 — Incident-level labels

Thermal recurrence is not the same target as confirmed fire occurrence.

For incident-level prediction/classification:

- collect trustworthy incident labels;
- align labels to satellite acquisition times and spatial uncertainty;
- distinguish routine industrial heat from emergency events;
- evaluate false-positive and false-negative costs;
- calibrate probabilities only after appropriate validation.

## Priority 4 — Production reliability

- persistent database for reports/subscriptions;
- observability and structured server logs;
- health metrics and alerting;
- provider retry/backoff policy;
- rate limiting backed by persistent/shared storage;
- scheduled model/data quality checks;
- deployment staging environment.

## Priority 5 — User experience

- richer historical timeline;
- state/district filters;
- clearer comparison of current vs normal thermal behaviour;
- downloadable evidence report;
- mobile optimization;
- accessible keyboard-first map alternatives;
- multilingual safety/explanation content.

## Non-goals until validated

AGNITE should not claim or imply:

- guaranteed fire occurrence;
- 99% real-world fire prediction accuracy;
- official emergency-alert authority;
- verified industrial causality from map proximity alone;
- continuous satellite surveillance.

## Release philosophy

A feature is considered complete only when:

1. implementation exists;
2. failure states are explicit;
3. tests/build pass;
4. provenance and limitations are documented;
5. the user-facing wording matches the actual validation level.
