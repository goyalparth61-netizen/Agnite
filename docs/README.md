# AGNITE Documentation Hub

Welcome to the technical and operational documentation for **AGNITE — AI-Powered Thermal Intelligence for India**.

> Team Timepass · Quantum University · Smart India Hackathon 2026 · SIH26162

## Start here

| Document | What it covers |
| --- | --- |
| [Architecture](ARCHITECTURE.md) | End-to-end system design, data flow, frontend, backend and intelligence layers |
| [API Reference](API.md) | HTTP endpoints, parameters, response behaviour and configuration |
| [ML Pipeline](ML_PIPELINE.md) | Thermal classifier, recurrence-model v2, training, thresholds and evaluation |
| [Data & Limitations](DATA_AND_LIMITATIONS.md) | Provenance, uncertainty, model scope and responsible claims |
| [Demo Guide](DEMO_GUIDE.md) | Judge-ready scenarios, 5-minute story, fallback path and expected questions |
| [Deployment](DEPLOYMENT.md) | Local, production and Render deployment instructions |
| [Project Structure](PROJECT_STRUCTURE.md) | Repository layout and module ownership |
| [Roadmap](ROADMAP.md) | Current completion state and the next validation/production milestones |
| [Demo datasets](../demo/README.md) | Reproducible industrial-spike, persistent-heat and natural-fire-style demo inputs |

## Current project state

AGNITE is a **feature-complete SIH MVP** with:

- live NASA FIRMS thermal-feed handling;
- interactive India-focused map exploration;
- historical baseline, trend, recurrence and persistence analysis;
- OSM / Overpass site context;
- explainable four-class thermal classification with abstention;
- a committed **NASA FIRMS thermal-recurrence model v2.0.0**;
- 24h / 48h / 7d recurrence windows;
- AGNITE AI local/provider modes;
- saved reports, watches, CSV workflows and optional email alerts;
- tests, production build and GitHub Actions CI.

### Recurrence validation snapshot

| Horizon | Precision | Recall | 99% precision target |
| --- | ---: | ---: | --- |
| 24h | 98.25% | 0.24% | Not met |
| 48h | 99.06% | 0.18% | Met |
| 7d | 99.06% | 0.55% | Met |

These figures apply only to **high-confidence thermal-recurrence decisions on the chronological held-out NASA FIRMS evaluation set**. They are not fire-incident accuracy.

## Product story

```text
DETECT → CONTEXTUALIZE → COMPARE HISTORY → CLASSIFY → ESTIMATE RECURRENCE → EXPLAIN → ACT
```

This story should stay consistent across the codebase, documentation and SIH presentation.

## Operational configuration

- [AGNITE AI provider configuration](../server/AI-CONFIG.md)
- [Email alert configuration](../server/ALERTS-CONFIG.md)
- [Environment variable template](../.env.example)
- [Render service definition](../render.yaml)

## Contribution and governance

- [Contributing](../CONTRIBUTING.md)
- [Security](../SECURITY.md)
- [Changelog](../CHANGELOG.md)
- [License](../LICENSE)

## Documentation standards

Every AGNITE document follows these rules:

1. **Provenance first.** Live NASA data, imported data, manual data and demo data must remain visibly distinct.
2. **Thermal detection ≠ confirmed fire.** Satellite detections are evidence, not incident ground truth.
3. **Metrics are scoped.** Synthetic validation, historical recurrence validation and real-world operational performance are never treated as interchangeable.
4. **Uncertainty stays visible.** Missing history, context gaps, stale feeds, abstention and low recall are documented rather than hidden.
5. **No inflated accuracy claims.** A 99% figure is quoted only with the exact task, dataset, threshold and metric that produced it.
