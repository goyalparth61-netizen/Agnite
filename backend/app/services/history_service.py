"""
History service for temporal statistics, overpass aggregation, and baseline computation.

Analyzes nearby observations, aggregates pixels belonging to the same satellite pass,
calculates median historical baseline (older than 24h), and emits chart-ready timeline data.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.schemas.analysis import HistoryTimelinePoint
from app.schemas.observation import Observation
from app.utils.dates import iso_to_epoch_ms, parse_utc_iso

DAY_MS = 86_400_000
HOUR_MS = 3_600_000


class PassAggregate(BaseModel):
    """Aggregated satellite overpass at a specific timestamp."""

    timestamp_ms: int
    observed_at: str
    mean_frp: float
    max_frp: float
    min_frp: float
    mean_brightness: Optional[float] = None
    sensor: Optional[str] = None
    pixel_count: int


class HotspotHistory(BaseModel):
    """Comprehensive temporal history summary for a hotspot."""

    observation_count: int
    distinct_passes_count: int
    first_observed_at: str
    latest_observed_at: str
    span_hours: float
    historical_duration_days: float
    unique_days_count: int
    calendar_span_days: int

    # FRP metrics based on pass means
    current_frp: float
    previous_frp: Optional[float] = None
    maximum_frp: float
    minimum_frp: float
    mean_frp: float
    median_frp: float
    frp_std: float

    # Baseline calculations
    baseline_frp: Optional[float] = None
    baseline_passes_count: int = 0
    frp_change: Optional[float] = None
    frp_change_percentage: Optional[float] = None
    log_baseline_ratio: float = 0.0

    # Timing intervals
    days_since_previous: Optional[float] = None
    detection_frequency: float = 0.0
    average_detection_interval_hours: Optional[float] = None

    # Series & Points
    passes: List[PassAggregate]
    timeline: List[HistoryTimelinePoint]


def _median(values: List[float]) -> float:
    """Compute median of numbers."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 1:
        return sorted_vals[mid]
    return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0


def _std(values: List[float], mean_val: float) -> float:
    """Compute population standard deviation."""
    if len(values) <= 1:
        return 0.0
    variance = sum((x - mean_val) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def compute_history(nearby_observations: List[Observation]) -> HotspotHistory:
    """
    Compute temporal history and baseline for a list of nearby observations.

    Expects nearby_observations to be sorted chronologically (oldest first).
    """
    if not nearby_observations:
        raise ValueError("Cannot compute history for empty observations list.")

    # 1. Group observations by exact acquisition timestamp (satellite overpass)
    grouped: Dict[int, List[Observation]] = defaultdict(list)
    for obs in nearby_observations:
        ts = iso_to_epoch_ms(obs.observed_at)
        grouped[ts].append(obs)

    sorted_timestamps = sorted(grouped.keys())
    passes: List[PassAggregate] = []

    for ts in sorted_timestamps:
        obs_list = grouped[ts]
        frps = [o.frp for o in obs_list]
        mean_f = sum(frps) / len(frps)
        max_f = max(frps)
        min_f = min(frps)

        # Brightness
        b_vals = [o.brightness for o in obs_list if o.brightness is not None]
        mean_b = sum(b_vals) / len(b_vals) if b_vals else None

        # Sensor
        sensors = [o.sensor for o in obs_list if o.sensor]
        sensor = sensors[0] if sensors else None

        passes.append(
            PassAggregate(
                timestamp_ms=ts,
                observed_at=obs_list[0].observed_at,
                mean_frp=mean_f,
                max_frp=max_f,
                min_frp=min_f,
                mean_brightness=mean_b,
                sensor=sensor,
                pixel_count=len(obs_list),
            )
        )

    first_ts = passes[0].timestamp_ms
    latest_ts = passes[-1].timestamp_ms
    span_hours = (latest_ts - first_ts) / HOUR_MS
    duration_days = span_hours / 24.0

    # Unique calendar days (UTC YYYY-MM-DD)
    dates = {parse_utc_iso(p.observed_at).strftime("%Y-%m-%d") for p in passes}
    unique_days_count = len(dates)

    first_day_epoch = first_ts // DAY_MS
    latest_day_epoch = latest_ts // DAY_MS
    calendar_span_days = max(1, latest_day_epoch - first_day_epoch + 1)
    detection_frequency = unique_days_count / calendar_span_days

    # Pass mean FRP distribution
    pass_frps = [p.mean_frp for p in passes]
    current_frp = passes[-1].mean_frp
    previous_frp = passes[-2].mean_frp if len(passes) >= 2 else None
    max_frp = max(pass_frps)
    min_frp = min(pass_frps)
    mean_frp = sum(pass_frps) / len(pass_frps)
    median_frp = _median(pass_frps)
    frp_std = _std(pass_frps, mean_frp)

    # Baseline: median of passes older than 24h before latest detection
    baseline_cutoff = latest_ts - DAY_MS
    baseline_passes = [p for p in passes if p.timestamp_ms < baseline_cutoff]
    baseline_frp = (
        _median([p.mean_frp for p in baseline_passes]) if baseline_passes else None
    )

    frp_change: Optional[float] = None
    frp_change_percentage: Optional[float] = None
    log_baseline_ratio: float = 0.0

    if baseline_frp is not None and baseline_frp > 0:
        frp_change = current_frp - baseline_frp
        frp_change_percentage = (current_frp / baseline_frp - 1.0) * 100.0
        log_baseline_ratio = math.log((current_frp + 1.0) / (baseline_frp + 1.0))
    elif baseline_frp is not None:
        frp_change = current_frp - baseline_frp
        log_baseline_ratio = math.log(current_frp + 1.0)

    # Intervals
    days_since_previous: Optional[float] = None
    if len(passes) >= 2:
        diff_ms = passes[-1].timestamp_ms - passes[-2].timestamp_ms
        days_since_previous = diff_ms / DAY_MS

    avg_interval_hours: Optional[float] = None
    if len(passes) >= 2:
        intervals = [
            (passes[i].timestamp_ms - passes[i - 1].timestamp_ms) / HOUR_MS
            for i in range(1, len(passes))
        ]
        avg_interval_hours = sum(intervals) / len(intervals)

    # Chart-ready timeline
    timeline: List[HistoryTimelinePoint] = [
        HistoryTimelinePoint(
            observedAt=p.observed_at,
            frp=round(p.mean_frp, 2),
            baseline=round(baseline_frp, 2) if baseline_frp is not None else None,
        )
        for p in passes
    ]

    return HotspotHistory(
        observation_count=len(nearby_observations),
        distinct_passes_count=len(passes),
        first_observed_at=passes[0].observed_at,
        latest_observed_at=passes[-1].observed_at,
        span_hours=round(span_hours, 2),
        historical_duration_days=round(duration_days, 2),
        unique_days_count=unique_days_count,
        calendar_span_days=calendar_span_days,
        current_frp=round(current_frp, 2),
        previous_frp=round(previous_frp, 2) if previous_frp is not None else None,
        maximum_frp=round(max_frp, 2),
        minimum_frp=round(min_frp, 2),
        mean_frp=round(mean_frp, 2),
        median_frp=round(median_frp, 2),
        frp_std=round(frp_std, 2),
        baseline_frp=round(baseline_frp, 2) if baseline_frp is not None else None,
        baseline_passes_count=len(baseline_passes),
        frp_change=round(frp_change, 2) if frp_change is not None else None,
        frp_change_percentage=(
            round(frp_change_percentage, 1)
            if frp_change_percentage is not None
            else None
        ),
        log_baseline_ratio=round(log_baseline_ratio, 4),
        days_since_previous=(
            round(days_since_previous, 2)
            if days_since_previous is not None
            else None
        ),
        detection_frequency=round(detection_frequency, 3),
        average_detection_interval_hours=(
            round(avg_interval_hours, 1)
            if avg_interval_hours is not None
            else None
        ),
        passes=passes,
        timeline=timeline,
    )
