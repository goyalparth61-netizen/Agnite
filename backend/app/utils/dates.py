"""
Date/time utilities for the AGNITE backend.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string with milliseconds and 'Z'."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def utc_now_ms() -> int:
    """Current UTC time as milliseconds since epoch."""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def parse_utc_iso(iso_str: str) -> datetime:
    """Parse ISO-8601 string (with 'Z' or offset) into UTC datetime."""
    clean = iso_str.strip()
    if clean.endswith("Z"):
        clean = clean[:-1] + "+00:00"
    dt = datetime.fromisoformat(clean)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def iso_to_epoch_ms(iso_str: str) -> int:
    """Parse ISO-8601 string to epoch milliseconds."""
    dt = parse_utc_iso(iso_str)
    return int(dt.timestamp() * 1000)


def epoch_ms_to_iso(ms: int | float) -> str:
    """Convert epoch milliseconds to ISO-8601 UTC string."""
    dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


_ACQ_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ACQ_TIME_RE = re.compile(r"^\d{1,4}$")


def acquisition_to_iso(date_str: str, time_str: str) -> str | None:
    """
    Convert NASA FIRMS acq_date + acq_time to ISO-8601 UTC string.

    Returns None if the inputs are invalid. Matches the Node server's
    ``acquisitionTime`` function exactly.
    """
    if not _ACQ_DATE_RE.match(date_str) or not _ACQ_TIME_RE.match(time_str):
        return None

    padded = time_str.zfill(4)
    hours = int(padded[:2])
    minutes = int(padded[2:])
    if hours > 23 or minutes > 59:
        return None

    iso = f"{date_str}T{padded[:2]}:{padded[2:]}:00.000Z"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        # Roundtrip check: reject nonsense dates like 2024-02-30
        if dt.strftime("%Y-%m-%dT%H:%M:%S.000Z") != iso:
            return None
        return iso
    except ValueError:
        return None
