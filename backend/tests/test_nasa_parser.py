"""
Tests for the NASA FIRMS CSV parser.

Uses static CSV fixtures — never calls live NASA APIs.
"""

from __future__ import annotations

import time

import pytest

from app.core.exceptions import FirmsError
from app.providers.nasa.parser import parse_firms_csv
from tests.conftest import (
    EMPTY_FIRMS_CSV,
    INVALID_HEADER_CSV,
    SAMPLE_FIRMS_CSV,
    SAMPLE_MODIS_CSV,
)


class TestParseFirmsCsv:
    """Test the NASA CSV parser with static fixtures."""

    def _now_ms(self) -> int:
        """Current time in ms, used as the 'now' reference for parsing."""
        return int(time.time() * 1000)

    def test_parses_valid_csv(self):
        """Valid VIIRS CSV produces normalized observations."""
        result = parse_firms_csv(
            SAMPLE_FIRMS_CSV, sensor="noaa20", hours=168, now_ms=self._now_ms()
        )
        assert isinstance(result["observations"], list)
        assert len(result["observations"]) > 0

    def test_observation_fields(self):
        """Each observation has all required frontend fields."""
        result = parse_firms_csv(
            SAMPLE_FIRMS_CSV, sensor="noaa20", hours=168, now_ms=self._now_ms()
        )
        obs = result["observations"][0]

        # Required by frontend validation
        assert isinstance(obs["id"], str)
        assert isinstance(obs["latitude"], float)
        assert isinstance(obs["longitude"], float)
        assert isinstance(obs["observedAt"], str)
        assert obs["observedAt"].endswith("Z")
        assert isinstance(obs["frp"], float)
        assert obs["source"] == "firms"
        assert obs["sensor"] == "noaa20"

    def test_observation_id_format(self):
        """IDs follow the firms-{sensor}-{satellite}-lat-lon-time format."""
        result = parse_firms_csv(
            SAMPLE_FIRMS_CSV, sensor="noaa20", hours=168, now_ms=self._now_ms()
        )
        obs = result["observations"][0]
        assert obs["id"].startswith("firms-noaa20-")

    def test_source_always_firms(self):
        """Every observation source must be 'firms'."""
        result = parse_firms_csv(
            SAMPLE_FIRMS_CSV, sensor="noaa20", hours=168, now_ms=self._now_ms()
        )
        for obs in result["observations"]:
            assert obs["source"] == "firms"

    def test_sensor_echoed(self):
        """Sensor is echoed into each observation."""
        for sensor in ("snpp", "noaa20", "modis"):
            csv = SAMPLE_FIRMS_CSV if sensor != "modis" else SAMPLE_MODIS_CSV
            result = parse_firms_csv(
                csv, sensor=sensor, hours=168, now_ms=self._now_ms()
            )
            for obs in result["observations"]:
                assert obs["sensor"] == sensor

    def test_latest_observation(self):
        """latestObservation is the most recent timestamp."""
        result = parse_firms_csv(
            SAMPLE_FIRMS_CSV, sensor="noaa20", hours=168, now_ms=self._now_ms()
        )
        if result["observations"]:
            assert result["latestObservation"] is not None
            assert result["latestObservation"] == result["observations"][0]["observedAt"]

    def test_empty_csv_returns_empty_list(self):
        """Header-only CSV returns empty observations, not an error."""
        result = parse_firms_csv(
            EMPTY_FIRMS_CSV, sensor="noaa20", hours=168, now_ms=self._now_ms()
        )
        assert result["observations"] == []
        assert result["latestObservation"] is None

    def test_invalid_header_raises(self):
        """CSV without required columns raises FirmsError."""
        with pytest.raises(FirmsError, match="missing required CSV columns"):
            parse_firms_csv(
                INVALID_HEADER_CSV, sensor="noaa20", hours=24, now_ms=self._now_ms()
            )

    def test_empty_document_raises(self):
        """Completely empty document raises FirmsError."""
        with pytest.raises(FirmsError, match="empty document"):
            parse_firms_csv("", sensor="noaa20", hours=24, now_ms=self._now_ms())

    def test_region_filtering(self):
        """Observations outside India region are excluded."""
        csv_outside = """\
latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti4,bright_ti5,frp,daynight,type
50.0000,10.0000,300.0,0.39,0.36,2026-09-13,1230,N20,nominal,2.0NRT,300.0,280.0,20.0,D,0
"""
        result = parse_firms_csv(
            csv_outside, sensor="noaa20", hours=168, now_ms=self._now_ms()
        )
        assert len(result["observations"]) == 0
        assert result["skipped"]["outsideRegion"] == 1

    def test_deduplication(self):
        """Duplicate observations (same id) are removed."""
        csv_dupes = """\
latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti4,bright_ti5,frp,daynight,type
21.1466,79.0889,338.5,0.39,0.36,2026-09-13,1230,N20,nominal,2.0NRT,313.2,289.1,45.2,D,0
21.1466,79.0889,338.5,0.39,0.36,2026-09-13,1230,N20,nominal,2.0NRT,313.2,289.1,45.2,D,0
"""
        result = parse_firms_csv(
            csv_dupes, sensor="noaa20", hours=168, now_ms=self._now_ms()
        )
        assert len(result["observations"]) == 1
        assert result["skipped"]["duplicates"] == 1

    def test_observation_limit(self):
        """Observations beyond max limit are skipped."""
        result = parse_firms_csv(
            SAMPLE_FIRMS_CSV,
            sensor="noaa20",
            hours=168,
            now_ms=self._now_ms(),
            max_observations=2,
        )
        assert len(result["observations"]) <= 2

    def test_confidence_preserved(self):
        """Confidence values (word or numeric) are preserved."""
        result = parse_firms_csv(
            SAMPLE_FIRMS_CSV, sensor="noaa20", hours=168, now_ms=self._now_ms()
        )
        confidences = [obs.get("confidence") for obs in result["observations"]]
        # Sample has nominal, high, low
        assert any(c in ("nominal", "high", "low") for c in confidences if c)

    def test_brightness_preserved(self):
        """Brightness values are preserved when present."""
        result = parse_firms_csv(
            SAMPLE_FIRMS_CSV, sensor="noaa20", hours=168, now_ms=self._now_ms()
        )
        obs_with_brightness = [
            obs for obs in result["observations"] if "brightness" in obs
        ]
        assert len(obs_with_brightness) > 0
        for obs in obs_with_brightness:
            assert isinstance(obs["brightness"], float)
            assert obs["brightness"] > 0

    def test_sorted_newest_first(self):
        """Observations are sorted newest first (matching Node server)."""
        result = parse_firms_csv(
            SAMPLE_FIRMS_CSV, sensor="noaa20", hours=168, now_ms=self._now_ms()
        )
        times = [obs["observedAt"] for obs in result["observations"]]
        assert times == sorted(times, reverse=True)

    def test_modis_csv(self):
        """MODIS-format CSV (brightness instead of bright_ti4) parses."""
        result = parse_firms_csv(
            SAMPLE_MODIS_CSV, sensor="modis", hours=168, now_ms=self._now_ms()
        )
        assert len(result["observations"]) > 0
        assert result["observations"][0]["sensor"] == "modis"
