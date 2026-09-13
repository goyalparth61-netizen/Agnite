"""
Domain constants shared across the AGNITE backend.

Sensor mappings, region bounds, time-window labels, analysis bounds,
risk thresholds, and persistence bands are defined here so that routes,
services, and providers all reference the same source.
"""

from __future__ import annotations

# ── India region bounding box ─────────────────────────────────────────
# The public NASA FIRMS CSV files for "South_Asia" already include this
# region plus neighbours.  We filter observations to this box.
INDIA_REGION = {
    "west": 67,
    "east": 99,
    "south": 6,
    "north": 38,
}

# ── Coverage label echoed to the frontend ─────────────────────────────
COVERAGE_LABEL = "India region bounding box, includes neighboring areas"

# ── Sensor → NASA download path mapping ──────────────────────────────
# Each sensor key maps to (folder_name, csv_prefix) used to build the
# public download URL.
SENSOR_PATHS: dict[str, tuple[str, str]] = {
    "snpp": ("viirs", "SUOMI_VIIRS_C2"),
    "noaa20": ("noaa-20-viirs-c2", "J1_VIIRS_C2"),
    "modis": ("modis-c6.1", "MODIS_C6_1"),
}

# ── Valid time windows (hours → NASA filename suffix) ─────────────────
WINDOW_LABELS: dict[int, str] = {
    24: "24h",
    48: "48h",
    168: "7d",
}

# ── Safety limits ─────────────────────────────────────────────────────
MAX_BODY_BYTES = 10 * 1024 * 1024        # 10 MB from NASA
MAX_OBSERVATIONS = 50_000                 # Upper bound per feed request
NASA_REQUEST_TIMEOUT_SECONDS = 25         # Abort if NASA doesn't respond

# ── Phase 2 Analysis Limits & Defaults ────────────────────────────────
DEFAULT_SEARCH_RADIUS_KM = 5.0
MIN_SEARCH_RADIUS_KM = 0.01
MAX_SEARCH_RADIUS_KM = 100.0
MAX_ANALYSIS_OBSERVATIONS = 5000

# ── Phase 2 Classification Classes ───────────────────────────────────
CLASS_INDUSTRIAL_FIRE = "Industrial Fire"
CLASS_PERSISTENT_HEAT = "Persistent Industrial Heat"
CLASS_FOREST_FIRE = "Forest / Natural Fire"
CLASS_OTHER_ANOMALY = "Other Thermal Anomaly"
CLASS_INSUFFICIENT_EVIDENCE = "Insufficient evidence"

VALID_CLASSIFICATIONS = [
    CLASS_INDUSTRIAL_FIRE,
    CLASS_PERSISTENT_HEAT,
    CLASS_FOREST_FIRE,
    CLASS_OTHER_ANOMALY,
    CLASS_INSUFFICIENT_EVIDENCE,
]

# ── Risk Level Thresholds (0-100) ────────────────────────────────────
RISK_LEVEL_CRITICAL_THRESHOLD = 75
RISK_LEVEL_HIGH_THRESHOLD = 55
RISK_LEVEL_MODERATE_THRESHOLD = 30

def get_risk_level(index: int) -> str:
    """Map numeric risk index (0-100) to severity tier."""
    if index >= RISK_LEVEL_CRITICAL_THRESHOLD:
        return "Critical"
    if index >= RISK_LEVEL_HIGH_THRESHOLD:
        return "High"
    if index >= RISK_LEVEL_MODERATE_THRESHOLD:
        return "Moderate"
    return "Low"

# ── Persistence Status Bands ──────────────────────────────────────────
PERSISTENCE_STATUS_INSUFFICIENT = "INSUFFICIENT_HISTORY"
PERSISTENCE_STATUS_LOW = "LOW_PERSISTENCE"
PERSISTENCE_STATUS_MODERATE = "MODERATE_PERSISTENCE"
PERSISTENCE_STATUS_HIGH = "HIGH_PERSISTENCE"

# ── Recurrence Signal Values ─────────────────────────────────────────
RECURRENCE_SIGNAL_INSUFFICIENT = "INSUFFICIENT_HISTORY"
RECURRENCE_SIGNAL_LOW = "LOW"
RECURRENCE_SIGNAL_MODERATE = "MODERATE"
RECURRENCE_SIGNAL_HIGH = "HIGH"

# ── Phase 3 OpenStreetMap Context Constants ───────────────────────────
DEFAULT_OSM_SEARCH_RADIUS_KM = 10.0
MIN_OSM_SEARCH_RADIUS_KM = 0.5
MAX_OSM_SEARCH_RADIUS_KM = 25.0

# Relevant OSM tag filters for Overpass QL queries
OSM_INDUSTRIAL_TAGS = [
    '["landuse"="industrial"]',
    '["industrial"]',
    '["man_made"="works"]',
    '["power"="plant"]',
    '["power"="generator"]',
    '["man_made"="chimney"]',
    '["man_made"="flare"]',
    '["man_made"="storage_tank"]',
    '["amenity"="fuel"]',
    '["landuse"="quarry"]',
]

# Source labels for provenance
CONTEXT_SOURCE_OSM = "OpenStreetMap"
CONTEXT_SOURCE_MANUAL = "Manual"
CONTEXT_SOURCE_UNKNOWN = "Unknown"

