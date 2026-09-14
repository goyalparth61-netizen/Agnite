# Data, Provenance and Limitations

## Purpose

AGNITE is designed to make uncertainty visible. This document defines what each data source means, what the models actually predict and which claims are responsible.

---

## NASA FIRMS

AGNITE uses NASA FIRMS near-real-time thermal detections for the live workspace and Standard Processing VIIRS history for recurrence-model training.

Supported live sources include:

- VIIRS NOAA-20
- VIIRS Suomi NPP
- MODIS Terra/Aqua

The server applies an India-region bounding box of approximately **6–38° N and 67–99° E**. This is a practical regional filter, not an exact political boundary.

A FIRMS hotspot is a satellite thermal detection. It does **not** by itself prove:

- a confirmed fire incident;
- industrial ownership or cause;
- emergency severity on the ground;
- continuous burning between satellite passes;
- the exact start or end time of an event.

Cloud, viewing geometry, overpass timing, sensor characteristics and detection thresholds can affect what appears in the feed.

---

## OpenStreetMap / Overpass

AGNITE uses OpenStreetMap / Overpass for nearby mapped context such as industrial land use, works, power facilities, forest, scrub, water and residential areas.

Limitations:

- community coverage may be incomplete;
- a mapped feature centre is not necessarily a facility boundary;
- proximity does not establish causality or ownership;
- mapped infrastructure may not reflect current operating status.

OSM context is supporting evidence, not ground truth.

---

## Imported and manual data

CSV and manual observations can be analyzed locally.

AGNITE does not independently verify their provenance. They remain labeled as `IMPORTED DATA` or `MANUAL DATA`.

Uploaded source strings other than the explicit `demo` label are normalized to imported provenance.

---

## Demo data

Demo scenarios are simulated by design.

They are useful for:

- judging demonstrations;
- UI walkthroughs;
- testing history/trend behaviour;
- comparing persistent vs rising thermal patterns.

They must never be presented as real NASA events.

The built-in industrial-spike scenario and the files under [`demo/`](../demo/README.md) are reproducible demonstration inputs.

---

## Historical baseline limitations

Historical intelligence is built from the observations actually available to the application.

It does not automatically reconstruct:

- missed satellite passes;
- cloud-obscured detections;
- non-detections;
- sensor outages;
- changes in satellite products;
- ground-truth incident timelines.

A sparse timeline means **limited observed evidence**, not necessarily no thermal activity.

---

## Thermal classifier limitations

The bundled thermal classifier is trained and evaluated on **synthetic archetypes**.

Current synthetic validation:

- 93.75% overall synthetic accuracy;
- 99.08% selective precision;
- 81.13% selective coverage.

These values are useful for validating pipeline behaviour and abstention logic, but they are **not field-validated fire-classification metrics**.

The system can return `Insufficient evidence` instead of forcing a class.

---

## Historical recurrence model limitations

The committed v2 recurrence model is trained from historical NASA FIRMS Standard Processing VIIRS observations.

Target:

> whether another FIRMS thermal detection appears in the same approximately 2 km spatial cell within 24h, 48h or 7d.

Current chronological held-out validation:

| Horizon | Precision | Recall | 99% target |
| --- | ---: | ---: | --- |
| 24h | 98.25% | 0.24% | Not met |
| 48h | 99.06% | 0.18% | Met |
| 7d | 99.06% | 0.55% | Met |

### Important interpretation

The 48h and 7d results are **high-precision, very-low-recall selective gates**.

This means:

- the model calls relatively few cases positive;
- precision is protected by a very strict threshold;
- many true recurrences are intentionally not called positive;
- the result is not a calibrated probability of a confirmed fire.

Do not present these metrics as “99% fire prediction accuracy.”

---

## Operational limitations

AGNITE is a decision-support prototype. It must not replace:

- emergency services;
- official disaster-management alerts;
- industrial safety procedures;
- field verification;
- qualified professional judgment.

Operational deployment would require additional validation, incident labels, monitoring, security hardening and integration with official workflows.

---

## Preferred presentation language

Use:

- “thermal detection” instead of “confirmed fire”;
- “thermal recurrence model” for repeat-FIRMS prediction;
- “high-confidence precision on held-out thermal-recurrence labels” when discussing the 99% gate;
- “synthetic selective validation” for the bundled classifier;
- “insufficient evidence” when the classifier abstains;
- “mapped context” rather than “verified cause” for OSM proximity.

Avoid:

- “99% accurate fire prediction”;
- “NASA confirmed this industrial fire”;
- “this facility caused the hotspot” based only on proximity;
- “continuous monitoring” when the evidence comes from discrete satellite passes.

---

## Responsible claim checklist

Before publishing a metric or statement, verify:

1. What exact target was predicted?
2. Which dataset produced the result?
3. Was validation synthetic, historical held-out or real-world field validation?
4. What threshold was used?
5. What were precision **and** recall / coverage?
6. Could the wording be misread as a stronger claim than the evidence supports?

If the answer to any of these is unclear, use a narrower claim.
