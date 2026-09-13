"""Reproducible, dependency-free SYNTHETIC thermal classifier experiment.

This is an educational multinomial logistic regression, not an operational
fire detector. Its held-out score measures simulated examples from this same
generator, and says nothing about performance on NASA FIRMS or field data.
Run: python scripts/train-thermal-model.py
"""

import json
import math
import random
from pathlib import Path

SEED = 41731
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
for x, actual in validation:
    predicted = max(range(4), key=lambda k: bias[k] + sum(w * v for w, v in zip(weights[k], x)))
    confusion[actual][predicted] += 1
accuracy = sum(confusion[k][k] for k in range(4)) / len(validation)
artifact = {
    "name": "AGNITE Synthetic Thermal Classifier",
    "version": "0.1.0",
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
    "confusionMatrix": confusion,
    "limitations": [
        "Trained and evaluated only on synthetic examples from the same generator.",
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
