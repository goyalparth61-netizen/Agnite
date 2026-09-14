# AGNITE Demo Scenarios

These datasets are **simulated demonstration inputs** for reproducible SIH walkthroughs. They are intentionally labeled `demo` and must not be presented as real NASA incidents.

## Included files

| File | Purpose | Thermal pattern |
| --- | --- | --- |
| `industrial-spike.csv` | Show a sudden abnormal rise after a lower baseline | 18 → 21 → 19 → 20 → 55 → 88 MW |
| `persistent-heat.csv` | Show repeated stable heat suitable for a persistent-heat discussion | ~30–35 MW |
| `natural-fire-rise.csv` | Show a rising thermal pattern that can be discussed with natural/forest context | 12 → 15 → 11 → 18 → 30 → 54 → 78 MW |

## How to use

1. Run AGNITE with `npm run dev`.
2. Open `/#/workspace?tab=import`.
3. Choose one CSV file.
4. Import the parsed observations.
5. Open **AGNITE AI / Analysis**.
6. Review the historical baseline, trend, classification evidence and missing context.
7. Open **Risk** to inspect the recurrence model.
8. Ask AGNITE AI a grounded question.

## Recommended questions

### Industrial spike

```text
What changed compared with the historical baseline, and what should be verified next?
```

### Persistent heat

```text
Does this look like a sudden abnormal event or a persistent thermal pattern, and why?
```

### Natural-fire-style rise

```text
How would forest or natural land-cover context change the interpretation of this rising signal?
```

## Important

The CSVs demonstrate **workflow behaviour**, not real-world model accuracy. Spatial context may be incomplete or unavailable depending on external map services, and the classifier may abstain when required evidence is missing.

For the full judging script see [`docs/DEMO_GUIDE.md`](../docs/DEMO_GUIDE.md).
