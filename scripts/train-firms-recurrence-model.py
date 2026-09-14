"""Train AGNITE's future thermal-recurrence models from historical NASA FIRMS CSV data.

What this predicts
------------------
This pipeline predicts whether another satellite thermal detection will occur in
approximately the same spatial cell within 24h, 48h, or 7d after a selected
observation. That is a measurable *thermal recurrence* target, not a guarantee
that a confirmed fire will occur.

Why this exists
---------------
The live AGNITE UI currently has a transparent heuristic risk simulation. This
script provides the real-data path needed to replace that heuristic once enough
historical FIRMS data have been collected. It uses a chronological holdout split
to avoid training on the future and learns an abstention threshold that targets
99% precision on the held-out data when the data support it. If 99% precision is
not achieved, the artifact records the actually achieved result instead of
fabricating a metric.

Input
-----
Pass one or more NASA FIRMS CSV exports (prefer Standard Processing historical
VIIRS data). Required columns: latitude, longitude, acq_date, acq_time, frp.
Useful optional columns: bright_ti4/brightness, bright_ti5, confidence, daynight,
type, satellite, instrument.

Example
-------
python -m pip install -r ml/requirements.txt
python scripts/train-firms-recurrence-model.py data/india_2024.csv data/india_2025.csv

Output
------
src/ai/recurrence-model.json

The exported model is deliberately simple (standardized logistic regression) so
it can be reproduced and ported to browser/Node inference without pickle files.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

INDIA = {"west": 67.0, "east": 99.0, "south": 6.0, "north": 38.0}
CELL_DEGREES = 0.02  # ~2 km latitude; used only to create a reproducible recurrence target.
HORIZONS_HOURS = {"24h": 24, "48h": 48, "7d": 24 * 7}
TARGET_PRECISION = 0.99
MIN_PREDICTED_POSITIVES = 25

FEATURES = [
    "log_current_frp",
    "log_frp_vs_7d_mean",
    "log_frp_vs_30d_mean",
    "detections_24h",
    "detections_7d",
    "detections_30d",
    "distinct_days_30d",
    "hours_since_previous",
    "bright_ti4_scaled",
    "bright_ti5_scaled",
    "confidence_scaled",
    "is_night",
    "static_source_type",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="NASA FIRMS CSV files")
    parser.add_argument(
        "--output",
        default="src/ai/recurrence-model.json",
        help="JSON artifact path",
    )
    parser.add_argument(
        "--validation-fraction",
        type=float,
        default=0.20,
        help="chronological holdout fraction (default: 0.20)",
    )
    return parser.parse_args()


def numeric_confidence(value: object) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0.5
    text = str(value).strip().lower()
    mapping = {"l": 0.25, "low": 0.25, "n": 0.60, "nominal": 0.60, "h": 0.90, "high": 0.90}
    if text in mapping:
        return mapping[text]
    try:
        return max(0.0, min(1.0, float(text) / 100.0))
    except ValueError:
        return 0.5


def timestamp_from_columns(frame: pd.DataFrame) -> pd.Series:
    acq_time = frame["acq_time"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(4)
    raw = frame["acq_date"].astype(str) + " " + acq_time.str[:2] + ":" + acq_time.str[2:4]
    return pd.to_datetime(raw, utc=True, errors="coerce")


def load_inputs(paths: Iterable[str]) -> pd.DataFrame:
    frames = []
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path, low_memory=False)
        frame.columns = [str(c).strip().lower() for c in frame.columns]
        missing = {"latitude", "longitude", "acq_date", "acq_time", "frp"} - set(frame.columns)
        if missing:
            raise ValueError(f"{path}: missing required columns {sorted(missing)}")
        frame["_source_file"] = path.name
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True)
    for column in ("latitude", "longitude", "frp", "bright_ti4", "brightness", "bright_ti5", "type"):
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    data["timestamp"] = timestamp_from_columns(data)
    data = data.dropna(subset=["timestamp", "latitude", "longitude", "frp"])
    data = data[
        data["latitude"].between(INDIA["south"], INDIA["north"])
        & data["longitude"].between(INDIA["west"], INDIA["east"])
        & data["frp"].ge(0)
    ].copy()
    if data.empty:
        raise ValueError("No valid India-region FIRMS observations remain after validation.")

    # A fixed spatial cell makes the recurrence label reproducible. It is not an
    # assertion that a fire footprint is exactly this size.
    data["cell_lat"] = (data["latitude"] / CELL_DEGREES).round().astype("int64")
    data["cell_lon"] = (data["longitude"] / CELL_DEGREES).round().astype("int64")
    data["cell"] = data["cell_lat"].astype(str) + ":" + data["cell_lon"].astype(str)

    bright4_col = "bright_ti4" if "bright_ti4" in data.columns else "brightness" if "brightness" in data.columns else None
    data["bright4"] = data[bright4_col] if bright4_col else np.nan
    data["bright5"] = data["bright_ti5"] if "bright_ti5" in data.columns else np.nan
    data["confidence_numeric"] = data["confidence"].map(numeric_confidence) if "confidence" in data.columns else 0.5
    data["is_night"] = data["daynight"].astype(str).str.upper().eq("N").astype(float) if "daynight" in data.columns else 0.0
    # NASA standard-processing VIIRS may expose Type=2 for an inferred other
    # static land source. This is useful context but is not an industrial-fire label.
    data["static_source_type"] = data["type"].eq(2).astype(float) if "type" in data.columns else 0.0

    # Collapse multiple pixels from the same cell/timestamp so dense pixel
    # clusters do not become duplicate temporal events.
    grouped = data.groupby(["cell", "timestamp"], as_index=False).agg(
        latitude=("latitude", "mean"),
        longitude=("longitude", "mean"),
        frp=("frp", "mean"),
        bright4=("bright4", "max"),
        bright5=("bright5", "max"),
        confidence_numeric=("confidence_numeric", "max"),
        is_night=("is_night", "max"),
        static_source_type=("static_source_type", "max"),
    )
    return grouped.sort_values(["cell", "timestamp"]).reset_index(drop=True)


def build_examples(events: pd.DataFrame) -> pd.DataFrame:
    """Create temporal examples without repeatedly scanning a cell's full history.

    The original implementation built boolean masks across every event for every
    event in a cell, which becomes very slow on multi-year FIRMS histories. This
    version uses binary-search window boundaries plus FRP prefix sums, preserving
    the same feature/label definitions while making the expensive history-window
    operations roughly O(n log n) instead of O(n^2) per cell.
    """
    columns = ["cell", "timestamp", *FEATURES, *(f"label_{name}" for name in HORIZONS_HOURS)]
    rows: list[tuple[object, ...]] = []
    grouped = events.groupby("cell", sort=False)
    cell_count = events["cell"].nunique()
    print(f"Building recurrence features from {len(events):,} grouped FIRMS events across {cell_count:,} cells...")

    for cell_index, (cell, group) in enumerate(grouped, start=1):
        group = group.sort_values("timestamp").reset_index(drop=True)
        n = len(group)
        times = group["timestamp"].to_numpy(dtype="datetime64[ns]")
        days = times.astype("datetime64[D]")
        frps = group["frp"].to_numpy(float)
        bright4 = group["bright4"].to_numpy(float)
        bright5 = group["bright5"].to_numpy(float)
        confidence = group["confidence_numeric"].to_numpy(float)
        is_night = group["is_night"].to_numpy(float)
        static_source = group["static_source_type"].to_numpy(float)
        prefix_frp = np.concatenate(([0.0], np.cumsum(frps, dtype=float)))

        for i in range(n):
            current = times[i]
            idx_24h = int(np.searchsorted(times, current - np.timedelta64(24, "h"), side="left"))
            idx_7d = int(np.searchsorted(times, current - np.timedelta64(7, "D"), side="left"))
            idx_30d = int(np.searchsorted(times, current - np.timedelta64(30, "D"), side="left"))

            count_7d = i - idx_7d
            count_30d = i - idx_30d
            mean7 = (
                float((prefix_frp[i] - prefix_frp[idx_7d]) / count_7d)
                if count_7d
                else float(frps[i])
            )
            mean30 = (
                float((prefix_frp[i] - prefix_frp[idx_30d]) / count_30d)
                if count_30d
                else mean7
            )
            previous_gap = (
                float((current - times[i - 1]) / np.timedelta64(1, "h"))
                if i
                else 24.0 * 30
            )
            distinct_days = int(np.unique(days[idx_30d:i]).size) if count_30d else 0
            next_time = times[i + 1] if i + 1 < n else None

            feature_values = (
                math.log1p(max(0.0, float(frps[i]))),
                math.log((float(frps[i]) + 1.0) / (mean7 + 1.0)),
                math.log((float(frps[i]) + 1.0) / (mean30 + 1.0)),
                i - idx_24h,
                count_7d,
                count_30d,
                distinct_days,
                min(previous_gap, 24.0 * 30) / 24.0,
                0.0 if np.isnan(bright4[i]) else max(0.0, min(500.0, float(bright4[i]))) / 500.0,
                0.0 if np.isnan(bright5[i]) else max(0.0, min(500.0, float(bright5[i]))) / 500.0,
                float(confidence[i]),
                float(is_night[i]),
                float(static_source[i]),
            )
            labels = tuple(
                int(next_time is not None and next_time <= current + np.timedelta64(hours, "h"))
                for hours in HORIZONS_HOURS.values()
            )
            rows.append((cell, pd.Timestamp(current, tz="UTC"), *feature_values, *labels))

        if cell_index % 10000 == 0 or cell_index == cell_count:
            print(f"  processed {cell_index:,}/{cell_count:,} cells; {len(rows):,} examples")

    examples = pd.DataFrame.from_records(rows, columns=columns)
    if len(examples) < 500:
        raise ValueError(f"Need at least 500 temporal examples; only {len(examples)} were created.")
    return examples.sort_values("timestamp").reset_index(drop=True)


def choose_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> dict[str, float | int | None]:
    best = None
    fallback = None
    for threshold in np.linspace(0.50, 0.999, 500):
        predicted = probabilities >= threshold
        count = int(predicted.sum())
        if count < MIN_PREDICTED_POSITIVES:
            continue
        precision = precision_score(y_true, predicted, zero_division=0)
        recall = recall_score(y_true, predicted, zero_division=0)
        candidate = (precision, recall, count, float(threshold))
        if fallback is None or candidate[:2] > fallback[:2]:
            fallback = candidate
        if precision >= TARGET_PRECISION:
            # Among thresholds meeting target precision, preserve the most recall.
            if best is None or (recall, count, -threshold) > (best[1], best[2], -best[3]):
                best = candidate
    chosen = best or fallback
    if chosen is None:
        return {
            "threshold": 1.0,
            "targetPrecision": TARGET_PRECISION,
            "achievedPrecision": None,
            "recallAtThreshold": 0.0,
            "predictedPositiveCount": 0,
            "targetMet": False,
        }
    precision, recall, count, threshold = chosen
    return {
        "threshold": threshold,
        "targetPrecision": TARGET_PRECISION,
        "achievedPrecision": float(precision),
        "recallAtThreshold": float(recall),
        "predictedPositiveCount": count,
        "targetMet": bool(precision >= TARGET_PRECISION),
    }


def safe_auc(metric, y_true: np.ndarray, probabilities: np.ndarray) -> float | None:
    if len(np.unique(y_true)) < 2:
        return None
    return float(metric(y_true, probabilities))


def train(examples: pd.DataFrame, validation_fraction: float) -> dict[str, object]:
    if not 0.10 <= validation_fraction <= 0.40:
        raise ValueError("validation fraction must be between 0.10 and 0.40")
    split = int(len(examples) * (1.0 - validation_fraction))
    train_frame = examples.iloc[:split]
    valid_frame = examples.iloc[split:]
    if train_frame.empty or valid_frame.empty:
        raise ValueError("Chronological split produced an empty train or validation set.")

    x_train = train_frame[FEATURES].to_numpy(float)
    x_valid = valid_frame[FEATURES].to_numpy(float)
    scaler = StandardScaler().fit(x_train)
    x_train_s = scaler.transform(x_train)
    x_valid_s = scaler.transform(x_valid)

    models: dict[str, object] = {}
    for horizon in HORIZONS_HOURS:
        label = f"label_{horizon}"
        y_train = train_frame[label].to_numpy(int)
        y_valid = valid_frame[label].to_numpy(int)
        if len(np.unique(y_train)) < 2:
            raise ValueError(f"Training data for {horizon} contains only one class.")
        clf = LogisticRegression(
            class_weight="balanced",
            max_iter=2500,
            solver="lbfgs",
            random_state=41731,
        ).fit(x_train_s, y_train)
        probabilities = clf.predict_proba(x_valid_s)[:, 1]
        default_prediction = probabilities >= 0.5
        gate = choose_threshold(y_valid, probabilities)
        models[horizon] = {
            "coefficient": clf.coef_[0].tolist(),
            "intercept": float(clf.intercept_[0]),
            "decisionThreshold": gate,
            "metrics": {
                "validationCount": int(len(y_valid)),
                "positiveRate": float(y_valid.mean()),
                "accuracyAt0_5": float(accuracy_score(y_valid, default_prediction)),
                "precisionAt0_5": float(precision_score(y_valid, default_prediction, zero_division=0)),
                "recallAt0_5": float(recall_score(y_valid, default_prediction, zero_division=0)),
                "f1At0_5": float(f1_score(y_valid, default_prediction, zero_division=0)),
                "rocAuc": safe_auc(roc_auc_score, y_valid, probabilities),
                "averagePrecision": safe_auc(average_precision_score, y_valid, probabilities),
            },
        }

    return {
        "trained": True,
        "name": "AGNITE NASA FIRMS Thermal Recurrence Model",
        "version": "1.0.0",
        "task": "Predict another FIRMS thermal detection in the same ~2 km spatial cell within each horizon; not a confirmed-fire forecast.",
        "trainingSource": "User-supplied historical NASA FIRMS CSV exports",
        "featureNames": FEATURES,
        "scaler": {"mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist()},
        "models": models,
        "validation": {
            "method": "chronological holdout; final observations reserved for validation",
            "trainCount": int(len(train_frame)),
            "validationCount": int(len(valid_frame)),
            "validationStart": valid_frame["timestamp"].min().isoformat(),
            "validationEnd": valid_frame["timestamp"].max().isoformat(),
            "targetPrecision": TARGET_PRECISION,
        },
        "spatialCellDegrees": CELL_DEGREES,
        "limitations": [
            "Predicts repeat satellite thermal detection, not a verified future fire incident.",
            "Cloud, overpass timing, sensor changes and missing detections can affect labels.",
            "A 99% precision target is reported only when achieved on the chronological holdout; no metric is guaranteed in advance.",
            "Validation should be repeated on later unseen years and, ideally, geographically held-out regions before operational claims.",
        ],
    }


def main() -> None:
    args = parse_args()
    events = load_inputs(args.inputs)
    examples = build_examples(events)
    artifact = train(examples, args.validation_fraction)
    artifact["sourceFiles"] = [Path(p).name for p in args.inputs]
    artifact["eventCount"] = int(len(events))
    artifact["exampleCount"] = int(len(examples))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {output} from {len(events):,} grouped FIRMS events / {len(examples):,} examples")
    for horizon, model in artifact["models"].items():
        gate = model["decisionThreshold"]
        precision = gate["achievedPrecision"]
        status = "TARGET MET" if gate["targetMet"] else "TARGET NOT MET"
        print(
            f"{horizon}: {status}; threshold={gate['threshold']:.3f}; "
            f"precision={precision if precision is not None else 'n/a'}; "
            f"recall={gate['recallAtThreshold']:.3f}"
        )


if __name__ == "__main__":
    main()
