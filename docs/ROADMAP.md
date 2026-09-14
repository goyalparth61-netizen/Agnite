# AGNITE Roadmap

## Current milestone — SIH MVP complete

The repository currently includes:

- India-focused interactive thermal workspace;
- live NASA FIRMS VIIRS/MODIS feed handling;
- explicit fresh / stale / unavailable provenance states;
- hotspot selection and nearby history;
- FRP baseline, deviation, trend, recurrence and persistence summaries;
- explainable synthetic-trained thermal classifier;
- conservative abstention / insufficient-evidence behaviour;
- OpenStreetMap / Overpass context;
- trained NASA FIRMS thermal-recurrence model v2;
- 24h / 48h / 7d recurrence windows;
- AGNITE AI local/provider modes;
- CSV import/export and reproducible demo datasets;
- saved reports and monitored locations;
- optional consent-based email alerts;
- production Node service and Render configuration;
- deterministic tests, production build and GitHub Actions CI;
- polished product flow, branding, Team Timepass identity and documentation.

For SIH demonstration purposes, the core feature set is **complete**. Remaining work is validation depth and production hardening rather than basic MVP functionality.

---

## Validation milestone achieved

A multi-year historical recurrence artifact has been trained and committed.

Current chronological holdout results:

| Horizon | Precision | Recall | Status |
| --- | ---: | ---: | --- |
| 24h | 98.25% | 0.24% | 99% target not met |
| 48h | 99.06% | 0.18% | 99% target met |
| 7d | 99.06% | 0.55% | 99% target met |

This moves AGNITE beyond a pure heuristic demo, while still leaving substantial validation work before operational claims.

---

## Priority 1 — Better predictive coverage

The current high-precision thresholds have very low recall.

Next work:

- evaluate precision-recall trade-offs across thresholds;
- compare Logistic Regression with tree/boosting models;
- add geographic holdout evaluation;
- validate on later unseen years;
- compare against simple persistence/baseline models;
- evaluate calibration if probability-like outputs are ever exposed;
- quantify drift by region, season and sensor.

Goal: improve useful coverage without hiding false-positive cost.

---

## Priority 2 — Real incident labels

Thermal recurrence is not the same target as confirmed fire occurrence.

For incident-level prediction/classification:

- acquire trustworthy fire and industrial-event labels;
- align incidents to satellite acquisition times and spatial uncertainty;
- distinguish routine industrial heat from emergency events;
- define false-positive / false-negative cost by use case;
- perform independent field or agency validation.

Only after this stage should AGNITE make incident-level operational performance claims.

---

## Priority 3 — Stronger context sources

- verified industrial facility datasets;
- reliable land-cover source;
- weather and wind observations / forecasts;
- terrain and fuel context where relevant;
- boundary-aware facility distance instead of centre-point proximity;
- state/district administrative boundaries.

---

## Priority 4 — Production reliability

- persistent database for reports/subscriptions;
- user authentication and role-aware workspaces if needed;
- structured observability and server logs;
- health metrics and alerting;
- persistent/shared rate limiting;
- provider retry/backoff policies;
- scheduled model and data-quality checks;
- deployment staging environment;
- automated security scanning.

---

## Priority 5 — User experience

- richer location timeline;
- side-by-side “current vs normal” visual comparison;
- multilingual explanations and safety content;
- downloadable evidence report / PDF;
- stronger mobile layout;
- accessible keyboard-first map alternative;
- state/district filters and saved investigations;
- public production deployment with real screenshots in README.

---

## Non-goals until validated

AGNITE should not claim or imply:

- guaranteed fire occurrence;
- 99% real-world fire prediction accuracy;
- official emergency-alert authority;
- verified industrial causality from mapped proximity alone;
- continuous satellite surveillance.

---

## Release philosophy

A feature is “done” only when:

1. implementation exists;
2. failure states are explicit;
3. tests/build pass;
4. provenance and limitations are documented;
5. user-facing wording matches the actual validation level.
