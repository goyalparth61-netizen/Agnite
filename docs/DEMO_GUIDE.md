# AGNITE Demo Guide

This guide is optimized for a short Smart India Hackathon judging session. The goal is to make the product story obvious even if live satellite services are slow or temporarily unavailable.

## Recommended demo strategy

Use this priority order:

1. **Live NASA FIRMS scenario** — best when an active hotspot has useful nearby history.
2. **Built-in industrial-spike demo** — deterministic and already available inside the workspace.
3. **Importable demo datasets** — use the files under [`demo/`](../demo/README.md) for controlled comparisons.

Never present demo rows as real NASA observations.

---

## Scenario A — live NASA FIRMS hotspot

### What to select

Do not pick a random dot. Prefer a hotspot that satisfies as many of these as possible:

- more than one nearby observation within ~5 km;
- visible FRP change or recurrence;
- a recognizable industrial or natural context;
- recent acquisition time;
- enough evidence for the analysis panel to show history rather than only a single point.

### Judge-facing flow

1. Open **Dashboard → Satellite feed**.
2. Keep **VIIRS NOAA-20** and start with the latest 24h window.
3. Select a hotspot with repeated or clearly elevated activity.
4. Show its acquisition time, FRP and source label.
5. Open **AGNITE AI / Analysis**.
6. Show baseline, trend, previous detections and mapped context.
7. Open **Risk** for 24h / 48h / 7d recurrence output.
8. Ask AGNITE AI: `Why is this hotspot risky and what evidence is missing?`
9. Finish with a saved report or monitoring action.

### Line to say

> “We do not treat a hotspot as a fire by default. AGNITE first asks what happened here before, what surrounds the location, how the current thermal signal differs from baseline and how confident the evidence actually is.”

---

## Scenario B — built-in industrial spike (recommended fallback)

The application includes a deterministic demo around **21.1466, 79.0889** with six daily observations and FRP values:

```text
18 → 21 → 19 → 20 → 55 → 88 MW
```

The built-in loader also supplies simulated industrial context so the complete analysis path is visible.

### Why this scenario works well

It gives a clear story:

- early observations establish a lower baseline;
- the last two observations rise sharply;
- the current signal is visibly abnormal relative to the earlier pattern;
- history, context, classification, recurrence and explainability can all be demonstrated in one location.

### How to present it

1. Click **Load demo scenario**.
2. Point out the **SIMULATED DATA** label immediately.
3. Open **AGNITE AI / Analysis**.
4. Explain the early baseline and late FRP rise.
5. Show the evidence/uncertainty panel.
6. Open **Risk** and explain that the committed v2 model predicts thermal recurrence, not a confirmed future fire.
7. Ask: `What changed compared with the historical baseline?`
8. Ask: `What should be verified before taking action?`

### Core line

> “The important part is not the number 88 by itself. AGNITE compares 88 MW with the history of the same place and explains why that change matters.”

---

## Scenario C — persistent industrial heat comparison

Import [`demo/persistent-heat.csv`](../demo/persistent-heat.csv).

This dataset stays near a stable thermal band across repeated days. Use it to contrast **persistent thermal behaviour** with the industrial-spike scenario.

### Talking points

- repeated heat is not automatically an emergency;
- recurrence and baseline stability matter;
- industrial context can explain why repeated thermal detections deserve a different interpretation;
- AGNITE can abstain when supporting context is incomplete.

Suggested question:

> `Does this look like a sudden abnormal event or a persistent thermal pattern, and why?`

---

## Scenario D — rising natural-fire-style pattern

Import [`demo/natural-fire-rise.csv`](../demo/natural-fire-rise.csv).

Use it to show that the same thermal logic can be evaluated with a different spatial context. If you use this scenario, explicitly state that the CSV is a **demo pattern**, not a verified forest-fire event.

Suggested question:

> `How would forest or natural land-cover context change the interpretation of this rising thermal pattern?`

---

## Five-minute SIH story

### 1. Problem — 30 seconds

> “Satellite systems can tell us that unusual heat exists, but they do not automatically explain whether it is recurring industrial heat, an abnormal event, what happened there before or what evidence should be checked next.”

Mention the core questions:

- What is happening now?
- Has it happened here before?
- Is the thermal pattern persistent or abnormal?
- What context exists around the location?
- What may happen in the next 24h / 48h / 7d?
- Why did the system reach that conclusion?

### 2. Map and provenance — 45 seconds

Show:

- NASA FIRMS source label;
- sensor and time-window controls;
- India map;
- selected hotspot;
- FRP and acquisition time.

Say:

> “These are satellite thermal detections, not automatically confirmed fires.”

### 3. Historical intelligence — 60 seconds

Show:

- previous detections;
- FRP history;
- baseline;
- trend;
- recurrence / persistence;
- nearby mapped context.

Say:

> “AGNITE does not look at a hotspot in isolation; it compares the current thermal behaviour with what happened at the same location before.”

### 4. Classification and explainability — 60 seconds

Open **AGNITE AI / Analysis** and show:

- classification or `Insufficient evidence`;
- supporting evidence;
- feature contributions;
- missing inputs / warnings.

Say:

> “If the evidence is weak, AGNITE abstains instead of forcing a confident answer.”

### 5. Thermal recurrence — 60 seconds

Open **Risk**.

Explain:

- 24h, 48h and 7d windows;
- model score vs conservative decision threshold;
- confidence state;
- validation scope.

Use the exact current validation statement:

> “On our chronological held-out NASA FIRMS recurrence task, the 48-hour and 7-day high-confidence gates reached about 99.06% precision. Recall is intentionally very low, so this is a selective alerting gate — not 99% overall fire accuracy.”

The 24h gate reached about **98.25% precision**, so the 99% target was **not** met there.

### 6. AGNITE AI and action — 45 seconds

Ask one grounded question:

- `Why was this hotspot classified this way?`
- `What changed compared with history?`
- `What evidence is missing?`
- `What should be verified next?`

Then briefly show alerts or saved reports.

---

## Best closing line

> “Most systems stop at showing where heat exists. AGNITE connects the past, present and possible next thermal state of that location, explains the evidence and helps the user decide what to inspect next.”

---

## If NASA or map services fail during judging

1. Do **not** refresh repeatedly in front of judges.
2. Use **Load demo scenario**.
3. Point to the **SIMULATED DATA** label.
4. Continue through analysis → risk → AGNITE AI.
5. Mention that AGNITE never silently replaces failed live NASA data with simulation.

This turns a network failure into a reliability point rather than a demo failure.

---

## Judge questions and strong answers

### “Is your model 99% accurate?”

> “No. We do not claim 99% fire-prediction accuracy. Our 48h and 7d conservative recurrence gates reached about 99.06% precision on chronological held-out NASA FIRMS thermal-recurrence labels, with very low recall. The 24h gate reached about 98.25%. That is a different and narrower claim.”

### “What exactly are you predicting?”

> “Whether another FIRMS thermal detection appears in the same approximately 2 km spatial cell within 24 hours, 48 hours or 7 days. That is not the same as predicting a confirmed fire incident.”

### “What is your innovation?”

> “Historical-location intelligence, persistent-heat separation, explainable classification, conservative future thermal-recurrence gates and an evidence-grounded assistant in one map-centric workflow.”

### “How do you separate industrial heat from fire?”

> “We combine thermal intensity and change, repeated detections, persistence, historical baseline, land-use context and industrial proximity. When those signals do not separate reliably, the system can abstain.”

### “What happens if NASA is unavailable?”

> “AGNITE shows an explicit failure or stale-cache state. It never silently substitutes demo data for NASA observations.”

### “Why is recall so low at the 99% precision gate?”

> “Because the threshold is deliberately conservative. We prefer a small number of very high-confidence recurrence positives over claiming certainty on every location. For broader coverage we would tune a different operating point and report the precision-recall trade-off.”

### “Is this ready for emergency response?”

> “It is a decision-support prototype. Operational deployment would require verified incident labels, field validation, calibrated models, stronger context sources and integration with official emergency workflows.”

---

## Final pre-demo checklist

- `git pull origin main`
- `npm test`
- `npm run build`
- homepage and `/#/workspace` open correctly
- AGNITE logo visible in navbar and workspace
- NASA source labels visible
- built-in demo works
- no secrets visible in browser or terminal
- recurrence metrics explained as precision/recall, not generic accuracy
- Team Timepass footer visible
- one team member owns the live flow and one owns backup/demo recovery
