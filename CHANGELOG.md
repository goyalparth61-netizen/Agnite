# Changelog

All notable repository-level changes are documented here.

## Unreleased

### Added

- Professional documentation hub under `docs/`.
- Judge-ready demo guide with live, built-in fallback and importable scenario paths.
- Reproducible demo datasets for industrial spike, persistent heat and rising natural-fire-style patterns.
- Polished README product preview and animated repository-star call to action.
- Prominent Team Timepass / Quantum University / SIH 2026 branding.
- Historical NASA FIRMS recurrence-model v2 trained on 2024–2025 Standard Processing VIIRS data.
- Enhanced v2 recurrence features covering temporal density, persistence, seasonality, acquisition time and coarse spatial interactions.
- Conservative per-horizon decision thresholds stored with the trained artifact.

### Changed

- README and documentation updated from “training-ready” to the actual committed v2 trained model state.
- Architecture documentation now reflects the active recurrence-model path.
- ML documentation now reports exact chronological holdout precision, recall and threshold values.
- Demo language now clearly separates thermal recurrence from confirmed fire prediction.
- Homepage and workspace branding now expose the AGNITE logo and a clearer user flow.

### Validation

Current recurrence-model v2 chronological holdout results:

- 24h: 98.25% precision, 0.24% recall — 99% precision target not met.
- 48h: 99.06% precision, 0.18% recall — target met.
- 7d: 99.06% precision, 0.55% recall — target met.

The model predicts repeat FIRMS thermal detection in the same spatial cell, not a confirmed future fire incident.

### Reliability

- CI verifies tests and production build.
- NASA-feed tests cover parsing, provenance, stale cache, size limits, timeouts and static serving safety.
- Intelligence tests cover temporal isolation, recurrence, assistant fallback and risk bounds.
- Frontend tests cover provenance labels, risk windows, optional location, documentation anchors and alert forms.

## 0.1.0

Initial AGNITE command-center prototype with:

- React + Vite + TypeScript frontend;
- Node.js API/static server;
- NASA FIRMS feed integration;
- interactive India-region workspace;
- synthetic thermal classifier;
- CSV import/export;
- saved reports and monitored locations;
- AGNITE assistant workflow;
- optional email notifications and external AI provider support.

> This changelog summarizes repository evolution and is not a deployment or model-validation record. Model metrics should be taken from the exact committed artifact and its evaluation output.
