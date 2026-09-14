# AGNITE Demo Guide

This guide is optimized for a short judging/demo session.

## 5-minute story

### 1. Problem — 30 seconds

Explain that satellite systems can show thermal hotspots, but users still need context:

- Is this recurring industrial heat or an unusual event?
- What happened at this location before?
- Is the current thermal signal above its own baseline?
- What may happen next?
- What evidence supports the result?

### 2. India thermal map — 45 seconds

Open the workspace and show:

- live NASA FIRMS source label;
- sensor and time-window controls;
- interactive hotspot map;
- FRP and acquisition time;
- site selection.

State explicitly that the points are thermal detections, not automatically confirmed fires.

### 3. Historical intelligence — 60 seconds

Select a location and show:

- previous detections within 5 km;
- FRP history;
- historical baseline;
- trend and recurrence/persistence;
- nearby mapped industrial/geographic context.

Core line:

> “AGNITE does not look at a hotspot in isolation; it compares the current thermal behaviour with what happened at the same location before.”

### 4. Classification and explainability — 60 seconds

Open **AGNITE AI / Analysis**.

Show:

- classification or `Insufficient evidence`;
- model evidence;
- feature contributions;
- data-quality warnings.

Core line:

> “If the evidence is weak, AGNITE abstains instead of forcing a confident answer.”

### 5. Future risk / recurrence — 60 seconds

Open **Risk** and show the 24h, 48h and 7d windows.

If no real recurrence model is trained, describe the cards as a **risk estimate / simulation**.

If a real recurrence artifact is trained, describe it as **historical thermal recurrence** and quote only the held-out metrics stored with that model.

Do not call a thermal-recurrence score “99% fire probability.”

### 6. AGNITE AI and action — 45 seconds

Ask a grounded question such as:

- “Why was this hotspot classified this way?”
- “What changed compared with its history?”
- “What evidence is missing?”
- “What precautions should be considered?”

Then briefly show alerts/reports.

## Recommended closing line

> “Most systems stop at showing where heat exists. AGNITE connects the past, present and possible next state of that location, explains the evidence and helps a user decide what to inspect next.”

## Offline / failure-safe path

If NASA or map services are temporarily unavailable:

1. use **Load demo scenario**;
2. clearly state that the observations are simulated;
3. demonstrate the same analysis, history, risk and AGNITE AI workflow;
4. never present demo values as live data.

## Judge questions

### “Is the model 99% accurate?”

Answer:

> “We do not claim 99% real-world fire-prediction accuracy. Our classifier can use a conservative high-precision gate on its synthetic validation set, and the real recurrence pipeline targets 99% precision on chronological held-out NASA FIRMS labels. We report that number only when the evaluation actually achieves it.”

### “What is your innovation?”

> “Historical-location intelligence plus persistent-heat separation, explainable classification, future thermal-recurrence/risk windows and an evidence-grounded assistant in one map-centric workflow.”

### “How do you separate industrial heat from fire?”

> “We combine thermal intensity/change, repeated detections, persistence, land-use/industrial proximity and history. When those signals do not separate reliably, the classifier abstains.”

### “What happens if NASA is down?”

> “AGNITE shows explicit failure or stale-cache state. It never silently replaces NASA observations with synthetic data.”

### “Is this ready for emergency response?”

> “It is a decision-support prototype. Field validation, verified incident labels, calibrated models and operational integrations are required before emergency deployment.”

## Final pre-demo checklist

- `npm test` passes;
- `npm run build` passes;
- live workspace route opens;
- NASA source labels are visible;
- demo fallback works;
- no secrets are visible in the browser;
- classification and risk limitations remain readable;
- AGNITE AI answers only from selected evidence;
- team members know the difference between detection, classification, risk index and recurrence prediction.
