# AGNITE ML Pipeline

## Scope

AGNITE currently has two distinct intelligence paths:

1. **thermal-source classification** for the selected hotspot context;
2. **future thermal-recurrence estimation** for 24h, 48h and 7d windows.

These are intentionally documented separately because they use different targets and validation assumptions.

## 1. Thermal-source classifier

### Candidate classes

- Industrial Fire
- Persistent Industrial Heat
- Forest / Natural Fire
- Other Thermal Anomaly

### Inputs

The local classifier uses derived features such as:

- current FRP;
- change relative to historical baseline;
- observation-day coverage/persistence;
- industrial proximity;
- land-cover category;
- wind input when supplied.

### Model

The bundled artifact is a multinomial logistic-regression experiment trained on seeded synthetic archetypes.

This makes the classifier useful for demonstrating pipeline behaviour, explainability and abstention, but **not** for claiming field-validated fire classification accuracy.

### Conservative abstention

AGNITE withholds a class when evidence is insufficient or ambiguous. Examples include:

- too few distinct passes;
- insufficient temporal span;
- too few baseline observations;
- unknown land cover or industrial distance;
- inputs outside the supported synthetic feature range;
- insufficient separation between the leading and runner-up classes.

The high-precision synthetic gate is intentionally selective: stronger precision is obtained by declining uncertain cases rather than forcing every input into a class.

A high precision measured on the synthetic holdout must be described exactly as a **synthetic selective-validation precision**, not real-world accuracy.

## 2. Historical NASA FIRMS recurrence model

### Target

The recurrence task is:

> Given a thermal detection and its previous history, estimate whether another NASA FIRMS thermal detection appears in the same spatial cell within 24 hours, 48 hours or 7 days.

This is **not equivalent to predicting a confirmed fire incident**.

### Data preparation

The repository includes:

- `scripts/download-firms-history.py`
- `scripts/train-firms-recurrence-model.py`
- `ml/requirements.txt`

The downloader is intended to collect historical FIRMS CSV data with a NASA FIRMS MAP_KEY. The training script builds temporal features, performs a time-aware split and writes the trained artifact to:

```text
src/ai/recurrence-model.json
```

The committed placeholder currently has `trained: false`. The application therefore falls back to the transparent heuristic future-risk simulation until a real artifact is generated.

### Feature families

The recurrence inference adapter supports features including:

- log FRP;
- FRP relative to recent 7-day and 30-day means;
- detection counts over 24h, 7d and 30d;
- distinct active days;
- time since previous detection;
- brightness/thermal channels when available;
- FIRMS confidence;
- approximate day/night context;
- hotspot type where available.

### Evaluation

The training path uses chronological holdout validation rather than randomly mixing future and past observations.

Each horizon stores:

- decision threshold;
- target precision;
- achieved precision;
- whether the target was met.

The current target is **0.99 precision** for the conservative positive-decision threshold.

The target is not treated as achieved unless the held-out evaluation actually reaches it.

### Precision vs accuracy

For AGNITE, these statements mean different things:

- **99% accuracy**: 99% of all evaluated samples were classified correctly. This is not currently established for real-world fire prediction.
- **99% precision**: among samples the conservative model marks positive, 99% were positive under the evaluation label definition.
- **99% precision on thermal recurrence** does not mean 99% probability that a real fire will occur.

If 99% precision requires very high abstention or very low recall, that limitation must be reported alongside precision.

## 3. Heuristic fallback

When no trained recurrence artifact exists, AGNITE computes a transparent 0–100 screening index using combinations of:

- current FRP intensity;
- deviation from baseline;
- recent trend;
- repeated detections;
- persistence;
- classification index;
- industrial proximity;
- land cover;
- wind input.

The UI labels this path **RISK ESTIMATE / SIMULATION**. It is not a learned forecast or event probability.

## 4. Explainability

The classification engine exposes model feature contributions when it produces a class. The risk and recurrence views expose the evidence used, missing inputs and threshold status.

AGNITE AI is expected to explain only the evidence available for the selected hotspot and to preserve uncertainty.

## 5. Reproducible training workflow

```powershell
python -m pip install -r ml/requirements.txt
$env:NASA_FIRMS_MAP_KEY="<your key>"

python scripts/download-firms-history.py `
  --start 2024-01-01 `
  --end 2026-08-31 `
  --source VIIRS_NOAA20_SP

$files = Get-ChildItem "data\firms\*.csv" | Select-Object -ExpandProperty FullName
python scripts/train-firms-recurrence-model.py @files
```

After training, inspect every horizon's validation metrics before committing the artifact.

## 6. Required reporting standard

Any presentation, README, paper or demo must state:

- exact task being predicted;
- data source;
- train/validation split method;
- validation sample size;
- precision, recall and threshold where relevant;
- whether the result is synthetic, historical held-out or field validated;
- that satellite thermal detections are not equivalent to confirmed incidents.

No metric should be generalized beyond the dataset and target on which it was measured.
