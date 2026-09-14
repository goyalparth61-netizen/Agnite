# AGNITE Documentation

This directory contains the technical and operational documentation for AGNITE.

## Start here

| Document | Purpose |
| --- | --- |
| [Architecture](ARCHITECTURE.md) | End-to-end system design, data flow, frontend, backend and intelligence layers |
| [API Reference](API.md) | Current HTTP endpoints, parameters, response behaviour and configuration |
| [ML Pipeline](ML_PIPELINE.md) | Classification, abstention, recurrence modelling, evaluation and accuracy policy |
| [Data & Limitations](DATA_AND_LIMITATIONS.md) | Source provenance, interpretation boundaries and responsible claims |
| [Deployment](DEPLOYMENT.md) | Local, production and Render deployment instructions |
| [Demo Guide](DEMO_GUIDE.md) | Recommended judging/demo flow and failure-safe presentation path |
| [Project Structure](PROJECT_STRUCTURE.md) | Repository layout and ownership boundaries between modules |
| [Roadmap](ROADMAP.md) | Completed capabilities and prioritized next validation work |

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

## Documentation principles

AGNITE documentation follows four rules:

1. **Live data is identified by provenance.** NASA data is never silently replaced by simulated data.
2. **Thermal detections are not treated as confirmed incidents.** Satellite evidence is described as evidence, not ground truth.
3. **Model metrics are scoped to the exact evaluation set.** Synthetic validation, held-out historical recurrence metrics and real-world operational performance are never presented as interchangeable.
4. **Uncertainty is visible.** Missing context, unavailable history, stale data and abstained classifications are surfaced instead of hidden.
