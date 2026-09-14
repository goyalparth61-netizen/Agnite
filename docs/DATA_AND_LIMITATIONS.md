# Data, Provenance and Limitations

## NASA FIRMS

AGNITE uses public NASA FIRMS near-real-time thermal detections for the live workspace. Supported sources are VIIRS NOAA-20, VIIRS Suomi NPP and MODIS Terra/Aqua.

The server applies an India-region bounding box of 6–38° N and 67–99° E. This includes neighboring areas and is not an exact political boundary.

A FIRMS hotspot is a satellite thermal detection. It does **not** by itself prove:

- a confirmed fire incident;
- industrial ownership or cause;
- severity on the ground;
- continuous burning between satellite passes;
- the exact start or end time of an event.

## OpenStreetMap / Overpass

AGNITE uses OpenStreetMap/Overpass to retrieve nearby industrial, power, land-use and natural features.

Limitations:

- community coverage may be incomplete;
- mapped feature centres are not facility boundaries;
- proximity does not establish containment;
- mapped infrastructure may not reflect current operating status.

## User-supplied context

Land cover, industrial distance and wind can be supplied or reviewed by the user. These inputs should be treated as assumptions unless independently verified.

## Imported and manual observations

CSV and manual data are accepted for local analysis. Their provenance is not independently verified by AGNITE. Imported/manual rows are labeled accordingly.

## Demo data

Demo scenarios are explicitly simulated and kept separate from non-demo histories. Demo values exist to demonstrate the product workflow and must not be presented as real NASA events.

## Historical baseline limits

Historical comparisons are built from supplied/loaded detections. Missing passes, clouds, sensor differences and non-detections are not automatically reconstructed. A sparse timeline therefore represents available evidence, not continuous observation.

## Model limitations

### Classifier

The bundled thermal classifier is synthetic-trained. It demonstrates explainable classification and abstention but is not field-validated.

### Future risk / recurrence

When `src/ai/recurrence-model.json` is untrained, AGNITE uses a heuristic simulation. A trained recurrence artifact predicts repeat FIRMS thermal detections under its label definition, not confirmed fires.

A validation metric is only valid for its exact dataset, target, split and threshold. AGNITE should never claim 99% real-world fire-prediction accuracy unless an appropriate real-world evaluation actually demonstrates it.

## Operational limitations

AGNITE is a decision-support prototype. It must not replace:

- emergency services;
- official disaster-management alerts;
- industrial safety procedures;
- field verification;
- qualified professional judgment.

## Responsible presentation language

Preferred language:

- “thermal detection” instead of “confirmed fire”;
- “risk estimate / simulation” when the heuristic fallback is active;
- “thermal recurrence model” for repeat-FIRMS prediction;
- “selected high-confidence precision” when using a selective threshold;
- “insufficient evidence” when the classifier abstains.

Avoid claims such as “99% accurate fire prediction” unless supported by a directly relevant, held-out real-world evaluation.
