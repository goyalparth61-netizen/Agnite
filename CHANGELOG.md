# Changelog

All notable repository-level changes are documented here.

## Unreleased

### Added

- Professional documentation set under `docs/`.
- Architecture, API, ML, deployment, demo, project-structure, roadmap and data-limitations guides.
- Contribution and security policies.
- Historical NASA FIRMS recurrence-model training path and runtime adapter.
- Conservative high-precision synthetic classifier abstention gate.
- Automatic mapped-context suggestions for land-cover/industrial-distance review.

### Changed

- Risk UI can distinguish heuristic simulation from a trained real-data recurrence model.
- Documentation now scopes all 99% claims to the exact validation target/evaluation rather than implying real-world fire-prediction accuracy.
- AGNITE AI and risk documentation now reflect local/provider modes and future recurrence workflow.

### Reliability

- CI verifies tests and production build.
- Model tests verify conservative abstention and finite/bounded outputs.
- Node ESM recurrence-module imports fixed for CI verification.

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
