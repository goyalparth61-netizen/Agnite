"""
NASA FIRMS CSV parser.

Parses the public near-real-time CSV download into normalized
``FirmsObservation`` objects.  This is a faithful port of the
Node.js ``parseFirmsCsv`` function in ``server/index.mjs``.

The parser is kept separate from the HTTP client so it can be
tested with static fixtures and swapped independently.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.core.constants import INDIA_REGION, MAX_BODY_BYTES, MAX_OBSERVATIONS
from app.core.exceptions import FirmsError
from app.utils.dates import acquisition_to_iso

logger = logging.getLogger(__name__)

_DECIMAL_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$", re.I)
_CONFIDENCE_WORD_RE = re.compile(r"^(l|low|n|nominal|h|high)$", re.I)


def _finite_number(value: str, minimum: float, maximum: float) -> float | None:
    """Parse a decimal string within bounds, or return None."""
    trimmed = value.strip()
    if not trimmed or not _DECIMAL_RE.match(trimmed):
        return None
    num = float(trimmed)
    if not (minimum <= num <= maximum) or num != num:  # NaN check
        return None
    return num


def _parse_csv_text(text: str) -> list[list[str]]:
    """
    Bounded CSV reader supporting quoted fields, escaped quotes,
    BOM, and CRLF.  Matches the Node server's parseCsv behaviour.
    """
    if len(text.encode("utf-8", errors="replace")) > MAX_BODY_BYTES:
        raise FirmsError("NASA FIRMS response exceeded the 10 MB safety limit.")

    rows: list[list[str]] = []
    row: list[str] = []
    field = ""
    quoted = False
    closed_quote = False

    csv = text.lstrip("\ufeff")

    for i in range(len(csv)):
        ch = csv[i]

        if quoted:
            if ch == '"':
                if i + 1 < len(csv) and csv[i + 1] == '"':
                    field += '"'
                    # Skip next char — we simulate index++ by continuing
                    # (handled below with a state flag)
                else:
                    quoted = False
                    closed_quote = True
            else:
                field += ch
            continue

        if ch == ",":
            row.append(field)
            if len(row) > 128:
                raise FirmsError("NASA FIRMS returned an invalid CSV row.")
            field = ""
            closed_quote = False
        elif ch in ("\n", "\r"):
            row.append(field)
            if any(v.strip() for v in row):
                rows.append(row)
            row = []
            field = ""
            closed_quote = False
        elif ch == '"' and field == "" and not closed_quote:
            quoted = True
        elif closed_quote or ch == '"':
            raise FirmsError("NASA FIRMS returned malformed CSV quoting.")
        else:
            field += ch

        if len(field) > 4096:
            raise FirmsError("NASA FIRMS returned an oversized CSV field.")

    if quoted:
        raise FirmsError("NASA FIRMS returned an unfinished CSV field.")

    # Final field / row
    if field or row or closed_quote:
        row.append(field)
        if any(v.strip() for v in row):
            rows.append(row)

    return rows


# We need to handle the escaped-quote skip that the simple loop above
# doesn't handle.  Re-implement with proper index control.


def _parse_csv(text: str) -> list[list[str]]:
    """
    Bounded CSV reader — proper implementation with index control
    for escaped quotes (``""``).
    """
    if len(text.encode("utf-8", errors="replace")) > MAX_BODY_BYTES:
        raise FirmsError("NASA FIRMS response exceeded the 10 MB safety limit.")

    rows: list[list[str]] = []
    row: list[str] = []
    field = ""
    quoted = False
    closed_quote = False

    csv = text.lstrip("\ufeff")
    i = 0
    length = len(csv)

    while i < length:
        ch = csv[i]

        if quoted:
            if ch == '"':
                if i + 1 < length and csv[i + 1] == '"':
                    field += '"'
                    i += 2
                    continue
                else:
                    quoted = False
                    closed_quote = True
                    i += 1
                    continue
            else:
                field += ch
                i += 1
                continue

        if ch == ",":
            row.append(field)
            if len(row) > 128:
                raise FirmsError("NASA FIRMS returned an invalid CSV row.")
            field = ""
            closed_quote = False
        elif ch == "\n" or ch == "\r":
            row.append(field)
            if any(v.strip() for v in row):
                rows.append(row)
            row = []
            field = ""
            closed_quote = False
            if ch == "\r" and i + 1 < length and csv[i + 1] == "\n":
                i += 1
        elif ch == '"' and field == "" and not closed_quote:
            quoted = True
        elif closed_quote or ch == '"':
            raise FirmsError("NASA FIRMS returned malformed CSV quoting.")
        else:
            field += ch

        if len(field) > 4096:
            raise FirmsError("NASA FIRMS returned an oversized CSV field.")

        i += 1

    if quoted:
        raise FirmsError("NASA FIRMS returned an unfinished CSV field.")

    if field or row or closed_quote:
        row.append(field)
        if any(v.strip() for v in row):
            rows.append(row)

    return rows


def parse_firms_csv(
    text: str,
    *,
    sensor: str = "snpp",
    hours: int = 24,
    now_ms: int | None = None,
    max_observations: int = MAX_OBSERVATIONS,
) -> dict[str, Any]:
    """
    Parse NASA FIRMS CSV text into normalized observation dicts.

    Returns a dict with:
      - observations: list of observation dicts
      - latestObservation: ISO string or None
      - warning: optional string
      - skipped: dict of skip counts

    This is a faithful port of the Node server's ``parseFirmsCsv``.
    """
    import time as _time

    if now_ms is None:
        now_ms = int(_time.time() * 1000)

    rows = _parse_csv(text)
    if not rows:
        raise FirmsError("NASA FIRMS returned an empty document instead of CSV.")

    header = [name.strip().lower() for name in rows[0]]
    data_rows = rows[1:]

    required = ["latitude", "longitude", "acq_date", "acq_time", "frp"]
    if len(set(header)) != len(header) or any(
        name not in header for name in required
    ):
        raise FirmsError("NASA FIRMS response is missing required CSV columns.")

    columns = {name: idx for idx, name in enumerate(header)}

    observations: list[dict[str, Any]] = []
    seen: set[str] = set()
    skipped = {
        "invalid": 0,
        "outsideRegion": 0,
        "outsideWindow": 0,
        "duplicates": 0,
        "overLimit": 0,
    }
    limit = max(1, min(MAX_OBSERVATIONS, max_observations))
    window_ms = hours * 60 * 60 * 1000
    future_tolerance_ms = 10 * 60 * 1000  # 10 minutes

    for row in data_rows:
        def val(name: str) -> str:
            idx = columns.get(name, -1)
            if idx < 0 or idx >= len(row):
                return ""
            return row[idx].strip()

        latitude = _finite_number(val("latitude"), -90, 90)
        longitude = _finite_number(val("longitude"), -180, 180)
        frp = _finite_number(val("frp"), 0, 1_000_000)
        acq = acquisition_to_iso(val("acq_date"), val("acq_time"))

        if (
            len(row) != len(header)
            or latitude is None
            or longitude is None
            or frp is None
            or acq is None
        ):
            skipped["invalid"] += 1
            continue

        # Parse timestamp for window/future checks
        from datetime import datetime, timezone

        try:
            dt = datetime.fromisoformat(acq.replace("Z", "+00:00"))
            timestamp_ms = int(dt.timestamp() * 1000)
        except ValueError:
            skipped["invalid"] += 1
            continue

        if timestamp_ms > now_ms + future_tolerance_ms:
            skipped["invalid"] += 1
            continue

        # Region filter
        if (
            latitude < INDIA_REGION["south"]
            or latitude > INDIA_REGION["north"]
            or longitude < INDIA_REGION["west"]
            or longitude > INDIA_REGION["east"]
        ):
            skipped["outsideRegion"] += 1
            continue

        # Window filter
        if timestamp_ms < now_ms - window_ms:
            skipped["outsideWindow"] += 1
            continue

        satellite = val("satellite")[:20]
        obs_id = (
            f"firms-{sensor}-{satellite}-"
            f"{latitude:.5f}-{longitude:.5f}-{acq}"
        )

        # Brightness
        brightness_key = "bright_ti4" if "bright_ti4" in columns else "brightness"
        brightness_text = val(brightness_key)
        brightness: float | None = None
        if brightness_text:
            brightness = _finite_number(brightness_text, 0, 10_000)
            if brightness is None:
                skipped["invalid"] += 1
                continue

        # Confidence
        confidence_text = val("confidence")
        confidence: str | float | None = None
        if confidence_text:
            if _CONFIDENCE_WORD_RE.match(confidence_text):
                confidence = confidence_text.lower()
            else:
                conf_num = _finite_number(confidence_text, 0, 100)
                if conf_num is None:
                    skipped["invalid"] += 1
                    continue
                confidence = conf_num

        # Dedup
        if obs_id in seen:
            skipped["duplicates"] += 1
            continue
        seen.add(obs_id)

        # Limit
        if len(observations) >= limit:
            skipped["overLimit"] += 1
            continue

        obs: dict[str, Any] = {
            "id": obs_id,
            "latitude": latitude,
            "longitude": longitude,
            "observedAt": acq,
            "frp": frp,
            "source": "firms",
            "sensor": sensor,
        }
        if brightness is not None:
            obs["brightness"] = brightness
        if confidence is not None:
            obs["confidence"] = confidence

        observations.append(obs)

    # Sort: descending observedAt, then ascending id (matches Node server)
    observations.sort(key=lambda o: o["id"])
    observations.sort(key=lambda o: o["observedAt"], reverse=True)

    # Build notes
    notes: list[str] = []
    if skipped["invalid"]:
        notes.append(f"{skipped['invalid']} invalid rows skipped")
    if skipped["outsideRegion"]:
        notes.append(
            f"{skipped['outsideRegion']} detections outside the India region "
            f"bounding box excluded"
        )
    if skipped["outsideWindow"]:
        notes.append(
            f"{skipped['outsideWindow']} detections outside the selected "
            f"time window excluded"
        )
    if skipped["duplicates"]:
        notes.append(f"{skipped['duplicates']} duplicate detections removed")
    if skipped["overLimit"]:
        notes.append(
            f"{skipped['overLimit']} detections omitted by the "
            f"{limit:,} record limit"
        )

    # A corrupt non-empty feed must never masquerade as empty
    if data_rows and skipped["invalid"] == len(data_rows):
        raise FirmsError("NASA FIRMS returned no valid CSV records.")

    result: dict[str, Any] = {
        "observations": observations,
        "latestObservation": observations[0]["observedAt"] if observations else None,
        "skipped": skipped,
    }
    if notes:
        result["warning"] = "; ".join(notes) + "."

    return result
