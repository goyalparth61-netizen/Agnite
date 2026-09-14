"""Reproducible, dependency-free SYNTHETIC thermal classifier experiment.

This is an educational multinomial logistic regression, not an operational
fire detector. Its held-out score measures simulated examples from this same
generator, and says nothing about performance on NASA FIRMS or field data.

The script also learns a conservative abstention gate. The gate targets at
least 99% precision on the held-out *synthetic* validation examples by only
returning a class when both the top softmax score and top-vs-second margin are
large enough. This improves precision by reducing coverage; it is NOT evidence
of 99% real-world accuracy.

Run: python scripts/train-thermal-model.py
"""

import json
import math
import random
from pathlib import Path

SEED = 41731
TARGET_SELECTIVE_PRECISION = 0.99
MIN_SELECTIVE_COVERAGE = 0.50
FEATURES = [
    "log_current_frp", "log_baseline_ratio", "observed_day_coverage",
    "industrial_proximity", "forest_cover", "industrial_cover", "urban_cover",
    "wind_scaled",
]
CLASSES = [
    "Industrial Fire", "Persistent Industrial Heat", "Forest / Natural Fire",
    "Other Thermal Anomaly",
]
rng = random.Random(SEED)


def example(label):
    # Distinct but overlapping synthetic archetypes, never real place labels.
    current = math.exp(rng.gauss([4.0, 3.5, 4.15, 2.45][label], 0.65))
    change = rng.gauss([1.5, 0.05, 1.25, 0.2][label], 0.5)
    recurrence = min(1, max(0.05, rng.gauss([0.6, 0.92, 0.65, 0.38][label], 0.19)))
    distance = max(0.02, rng.gauss([1.0, 0.65, 18.0, 10.0][label], [1.2, 0.8, 10, 8][label]))
    covers = ["industrial", "industrial", "forest", "other"]
    cover = covers[label] if rng.random() < 0.82 else rng.choice(["forest", "urban", "industrial", "other"])
    wind = max(0, rng.gauss([14, 11, 22, 12][label], 10))
    return [
        math.log1p(current), change, recurrence, 1 / (1 + distance / 2),
        float(cover == "forest"), float(cover == "industrial"), float(cover == "urban"),
        min(wind, 100) / 50,
    ], label


def softmax(values):
    largest = max(values)
    exps = [math.exp(v - largest) for v in values]
    total = sum(exps)
    return [v / total for v in exps]


train = [example(label) for label in range(4) for _ in range(650)]
validation = [example(label) for label in range(4) for _ in range(200)]
rng.shuffle(train)
means = [sum(x[j] for x, _ in train) / len(train) for j in range(len(FEATURES))]
scales = [math.sqrt(sum((x[j] - means[j]) ** 2 for x, _ in train) / len(train)) or 1 for j in range(len(FEATURES))]


def standardize(x):
    return [(v - means[j]) / scales[j] for j, v in enumerate(x)]


train = [(standardize(x), y) for x, y in train]
validation = [(standardize(x), y) for x, y in validation]
weights = [[0.0] * len(FEATURES) for _ in CLASSES]
bias = [0.0] * len(CLASSES)
# Batch gradient descent with L2 regularization; no nonstandard packages.
for epoch in range(360):
    gradients = [[0.0] * len(FEATURES) for _ in CLASSES]
    bias_gradients = [0.0] * len(CLASSES)
    for x, label in train:
        probs = softmax([bias[k] + sum(w * v for w, v in zip(weights[k], x)) for k in range(4)])
        for k in range(4):
            error = probs[k] - float(label == k)
            bias_gradients[k] += error
            for j in range(len(FEATURES)):
                gradients[k][j] += error * x[j]
    for k in range(4):
        bias[k] -= 0.16 * bias_gradients[k] / len(train)
        for j in range(len(FEATURES)):
            weights[k][j] -= 0.16 * (gradients[k][j] / len(train) + 0.004 * weights[k][j])

confusion = [[0] * 4 for _ in CLASSES]
validation_rows = []
for x, actual in validation:
    logits = [bias[k] + sum(w * v for w, v in zip(weights[k], x)) for k in range(4)]
    probs = softmax(logits)
    ranked = sorted(range(4), key=lambda k: probs[k], reverse=True)
    predicted = ranked[0]
    confusion[actual][predicted] += 1
    validation_rows.append({
        "correct": predicted == actual,
        "score": probs[ranked[0]],
        "margin": probs[ranked[0]] - probs[ranked[1]],
    })
accuracy = sum(confusion[k][k] for k in range(4)) / len(validation)

# Find the broadest conservative gate that reaches the requested precision on
# synthetic validation. Both score and margin are searched because a high top
# score with a close runner-up is still ambiguous.
best_gate = None
for score_step in range(500, 1000, 5):
    score_threshold = score_step / 1000
    for margin_step in range(100, 1000, 5):
        margin_threshold = margin_step / 1000
        selected = [
            row for row in validation_rows
            if row["score"] >= score_threshold and row["margin"] >= margin_threshold
        ]
        if not selected:
            continue
        coverage = len(selected) / len(validation_rows)
        precision = sum(row["correct"] for row in selected) / len(selected)
        if coverage < MIN_SELECTIVE_COVERAGE or precision < TARGET_SELECTIVE_PRECISION:
            continue
        candidate = (coverage, precision, score_threshold, margin_threshold, len(selected))
        if best_gate is None or candidate[:2] > best_gate[:2]:
            best_gate = candidate

if best_gate is None:
    # Conservative fallback: preserve abstention rather than manufacturing a
    # target metric that was not achieved.
    selective = {
        "targetPrecision": TARGET_SELECTIVE_PRECISION,
        "achievedPrecision": None,
        "coverage": 0.0,
        "scoreThreshold": 1.0,
        "marginThreshold": 1.0,
        "selectedCount": 0,
        "validatedOn": "synthetic held-out examples only",
    }
else:
    coverage, precision, score_threshold, margin_threshold, selected_count = best_gate
    selective = {
        "targetPrecision": TARGET_SELECTIVE_PRECISION,
        "achievedPrecision": precision,
        "coverage": coverage,
        "scoreThreshold": score_threshold,
        "marginThreshold": margin_threshold,
        "selectedCount": selected_count,
        "validatedOn": "synthetic held-out examples only",
    }

artifact = {
    "name": "AGNITE Synthetic Thermal Classifier",
    "version": "0.2.0",
    "algorithm": "multinomial logistic regression, L2 regularization",
    "trainingSource": "Seeded synthetic archetypes only; no satellite or field labels",
    "seed": SEED,
    "featureNames": FEATURES,
    "classes": CLASSES,
    "means": means,
    "scales": scales,
    "weights": weights,
    "bias": bias,
    "trainingCount": len(train),
    "validationCount": len(validation),
    "syntheticValidationAccuracy": accuracy,
    "selectiveValidation": selective,
    "confusionMatrix": confusion,
    "limitations": [
        "Trained and evaluated only on synthetic examples from the same generator.",
        "The selective gate may exceed 99% precision on synthetic validation by abstaining on ambiguous cases; this is not real-world accuracy.",
        "No real-world validation, calibrated confidence, or operational fire identification.",
        "Observation selection and cloud cover can bias historical comparisons and recurrence.",
        "Land cover and industrial distance are supplied by the user, not independently verified.",
        "Risk and what-if scenarios are separate heuristics, not model forecasts or fire probabilities.",
    ],
}
target = Path(__file__).resolve().parents[1] / "src" / "ai" / "model.json"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
print(f"Saved {target.name}: {len(train)} synthetic training / {len(validation)} synthetic validation examples")
print(f"Synthetic validation accuracy: {accuracy:.3%}; NOT a real-world accuracy claim")
if selective["achievedPrecision"] is None:
    print("Selective gate could not reach the requested precision at minimum coverage.")
else:
    print(
        "Selective synthetic precision: "
        f"{selective['achievedPrecision']:.3%} at {selective['coverage']:.1%} coverage; "
        "NOT a real-world accuracy claim"
    )
