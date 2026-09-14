"""Train AGNITE recurrence model v2 with richer temporal, seasonal and persistence features.

This script predicts repeat NASA FIRMS thermal detections, not confirmed future fires.
It keeps the exported artifact browser/Node portable by using standardized logistic
regression, while adding nonlinear hand-engineered signals that can be reproduced
exactly at runtime.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path

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

BASE_PATH = Path(__file__).with_name("train-firms-recurrence-model.py")
spec = importlib.util.spec_from_file_location("agnite_recurrence_base", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load {BASE_PATH}")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

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
    "log_detections_24h",
    "log_detections_7d",
    "log_detections_30d",
    "persistence_7d_30d",
    "active_days_ratio_30d",
    "log_gap_hours",
    "recent_repeat_48h",
    "frp_x_log_detections_7d",
    "frp_x_static_source",
    "night_x_log_detections_7d",
    "month_sin",
    "month_cos",
    "hour_sin",
    "hour_cos",
    "latitude_scaled",
    "longitude_scaled",
    "lat_lon_interaction",
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


def build_examples(events: pd.DataFrame) -> pd.DataFrame:
    columns = ["cell", "timestamp", *FEATURES, *(f"label_{name}" for name in HORIZONS_HOURS)]
    rows: list[tuple[object, ...]] = []
    grouped = events.groupby("cell", sort=False)
    cell_count = events["cell"].nunique()
    print(
        f"Building enhanced recurrence features from {len(events):,} grouped FIRMS events "
        f"across {cell_count:,} cells..."
    )

    for cell_index, (cell, group) in enumerate(grouped, start=1):
        group = group.sort_values("timestamp").reset_index(drop=True)
        n = len(group)
        times = group["timestamp"].to_numpy(dtype="datetime64[ns]")
        days = times.astype("datetime64[D]")
        frps = group["frp"].to_numpy(float)
        latitudes = group["latitude"].to_numpy(float)
        longitudes = group["longitude"].to_numpy(float)
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

            count24 = i - idx_24h
            count7 = i - idx_7d
            count30 = i - idx_30d
            mean7 = float((prefix_frp[i] - prefix_frp[idx_7d]) / count7) if count7 else float(frps[i])
            mean30 = float((prefix_frp[i] - prefix_frp[idx_30d]) / count30) if count30 else mean7
            previous_gap = float((current - times[i - 1]) / np.timedelta64(1, "h")) if i else 24.0 * 30
            previous_gap = min(max(previous_gap, 0.0), 24.0 * 30)
            distinct_days = int(np.unique(days[idx_30d:i]).size) if count30 else 0
            next_time = times[i + 1] if i + 1 < n else None

            timestamp = pd.Timestamp(current, tz="UTC")
            month_angle = 2.0 * math.pi * (timestamp.month - 1) / 12.0
            hour_angle = 2.0 * math.pi * (timestamp.hour + timestamp.minute / 60.0) / 24.0
            log_frp = math.log1p(max(0.0, float(frps[i])))
            log_count24 = math.log1p(count24)
            log_count7 = math.log1p(count7)
            log_count30 = math.log1p(count30)
            lat_scaled = (float(latitudes[i]) - 22.0) / 16.0
            lon_scaled = (float(longitudes[i]) - 83.0) / 16.0

            feature_values = (
                log_frp,
                math.log((float(frps[i]) + 1.0) / (mean7 + 1.0)),
                math.log((float(frps[i]) + 1.0) / (mean30 + 1.0)),
                count24,
                count7,
                count30,
                distinct_days,
                previous_gap / 24.0,
                0.0 if np.isnan(bright4[i]) else max(0.0, min(500.0, float(bright4[i]))) / 500.0,
                0.0 if np.isnan(bright5[i]) else max(0.0, min(500.0, float(bright5[i]))) / 500.0,
                float(confidence[i]),
                float(is_night[i]),
                float(static_source[i]),
                log_count24,
                log_count7,
                log_count30,
                count7 / max(1.0, float(count30)),
                distinct_days / 30.0,
                math.log1p(previous_gap),
                float(previous_gap <= 48.0),
                log_frp * log_count7,
                log_frp * float(static_source[i]),
                float(is_night[i]) * log_count7,
                math.sin(month_angle),
                math.cos(month_angle),
                math.sin(hour_angle),
                math.cos(hour_angle),
                lat_scaled,
                lon_scaled,
                lat_scaled * lon_scaled,
            )
            labels = tuple(
                int(next_time is not None and next_time <= current + np.timedelta64(hours, "h"))
                for hours in HORIZONS_HOURS.values()
            )
            rows.append((cell, timestamp, *feature_values, *labels))

        if cell_index % 10000 == 0 or cell_index == cell_count:
            print(f"  processed {cell_index:,}/{cell_count:,} cells; {len(rows):,} examples")

    examples = pd.DataFrame.from_records(rows, columns=columns)
    if len(examples) < 500:
        raise ValueError(f"Need at least 500 temporal examples; only {len(examples)} were created.")
    return examples.sort_values("timestamp").reset_index(drop=True)


def choose_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> dict[str, float | int | None]:
    # Evaluate exact score cut points instead of a coarse fixed grid. This can
    # find a better high-precision operating point without relaxing the minimum
    # support requirement.
    order = np.argsort(-probabilities)
    y_sorted = y_true[order]
    p_sorted = probabilities[order]
    tp = np.cumsum(y_sorted)
    predicted = np.arange(1, len(y_sorted) + 1)
    precision = tp / predicted
    total_positive = max(1, int(y_true.sum()))
    recall = tp / total_positive

    eligible = predicted >= MIN_PREDICTED_POSITIVES
    target_candidates = np.where(eligible & (precision >= TARGET_PRECISION))[0]
    if len(target_candidates):
        # Highest recall among target-meeting points; ties naturally prefer more support.
        best_idx = int(target_candidates[np.argmax(recall[target_candidates])])
        target_met = True
    else:
        eligible_indices = np.where(eligible)[0]
        if not len(eligible_indices):
            return {
                "threshold": 1.0,
                "targetPrecision": TARGET_PRECISION,
                "achievedPrecision": None,
                "recallAtThreshold": 0.0,
                "predictedPositiveCount": 0,
                "targetMet": False,
            }
        best_precision = precision[eligible_indices].max()
        candidates = eligible_indices[precision[eligible_indices] == best_precision]
        best_idx = int(candidates[np.argmax(recall[candidates])])
        target_met = False

    threshold = float(p_sorted[best_idx])
    return {
        "threshold": threshold,
        "targetPrecision": TARGET_PRECISION,
        "achievedPrecision": float(precision[best_idx]),
        "recallAtThreshold": float(recall[best_idx]),
        "predictedPositiveCount": int(predicted[best_idx]),
        "targetMet": target_met,
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
        "version": "2.0.0",
        "task": "Predict another FIRMS thermal detection in the same ~2 km spatial cell within each horizon; not a confirmed-fire forecast.",
        "trainingSource": "Historical NASA FIRMS Standard Processing VIIRS observations",
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
        "spatialCellDegrees": base.CELL_DEGREES,
        "featureEngineering": "v2 temporal density, persistence interactions, seasonality, acquisition time and coarse spatial terms",
        "limitations": [
            "Predicts repeat satellite thermal detection, not a verified future fire incident.",
            "Cloud, overpass timing, sensor changes and missing detections can affect labels.",
            "A 99% precision target is reported only when achieved on the chronological holdout; no metric is guaranteed in advance.",
            "Validation should be repeated on later unseen years and geographically held-out regions before operational claims.",
        ],
    }


def main() -> None:
    args = parse_args()
    events = base.load_inputs(args.inputs)
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
            f"{horizon}: {status}; threshold={gate['threshold']:.6f}; "
            f"precision={precision if precision is not None else 'n/a'}; "
            f"recall={gate['recallAtThreshold']:.4f}; "
            f"predicted={gate['predictedPositiveCount']}"
        )


if __name__ == "__main__":
    main()
