"""
Parser for OpenStreetMap Overpass API responses.

Normalizes raw Overpass JSON elements (nodes, ways, relations) into typed
OsmFeature records, calculates Haversine distance from the query center,
and classifies infrastructure into standardized categories.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.context import NearestFeatureSummary, OsmFeature
from app.utils.geo import haversine_km, is_valid_coordinate

logger = logging.getLogger("app.providers.osm.parser")


def classify_osm_feature_type(tags: Dict[str, str]) -> str:
    """Classify OSM element into standardized infrastructure category based on tags and name."""
    man_made = tags.get("man_made", "").lower()
    power = tags.get("power", "").lower()
    landuse = tags.get("landuse", "").lower()
    industrial = tags.get("industrial", "").lower()
    name = tags.get("name", "").lower()

    # 1. Thermal & emission structures
    if man_made == "flare":
        return "flare"
    if man_made == "chimney":
        return "chimney"

    # 2. Power infrastructure
    if power in ("plant", "generator") or "power plant" in name or "power station" in name:
        return "power_plant"
    if power == "substation":
        return "power_substation"

    # 3. High-heat & Heavy Industry sub-types
    if any(k in industrial or k in name for k in ("refinery", "oil", "petroleum", "gas")):
        return "refinery"
    if any(k in industrial or k in name for k in ("steel", "metallurgy", "foundry", "smelter", "blast furnace")):
        return "metal_works"
    if any(k in industrial or k in name for k in ("chemical", "fertilizer", "pharmaceutical")):
        return "chemical_plant"
    if any(k in industrial or k in name for k in ("cement", "brick", "kiln")):
        return "cement_works"

    # 4. General Works & Factories
    if man_made == "works" or industrial:
        return "factory"

    # 5. Industrial Landuse
    if landuse == "industrial":
        return "industrial_area"

    # 6. Storage & Fuel
    if man_made == "storage_tank":
        return "storage_tank"
    if tags.get("amenity") == "fuel":
        return "fuel_infrastructure"

    # 7. Mining / Extraction
    if landuse == "quarry":
        return "quarry"

    return "industrial_other"


def extract_coordinates(element: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    """
    Extract (lat, lon) safely from node, way, or relation element.

    Checks:
    1. element.lat and element.lon (nodes, or top-level element coords)
    2. element.center.lat and element.center.lon (ways and relations via 'out center tags;')
    3. element.bounds (midpoint fallback)
    """
    # 1. Direct lat/lon on element
    lat = element.get("lat")
    lon = element.get("lon")
    if lat is not None and lon is not None:
        try:
            flat = float(lat)
            flon = float(lon)
            if is_valid_coordinate(flat, flon):
                return flat, flon
        except (ValueError, TypeError):
            pass

    # 2. 'center' dictionary (for ways and relations from 'out center tags;')
    center = element.get("center")
    if isinstance(center, dict):
        clat = center.get("lat")
        clon = center.get("lon")
        if clat is not None and clon is not None:
            try:
                flat = float(clat)
                flon = float(clon)
                if is_valid_coordinate(flat, flon):
                    return flat, flon
            except (ValueError, TypeError):
                pass

    # 3. Fallback to bounds midpoint if available
    bounds = element.get("bounds")
    if isinstance(bounds, dict):
        try:
            minlat = bounds.get("minlat")
            maxlat = bounds.get("maxlat")
            minlon = bounds.get("minlon")
            maxlon = bounds.get("maxlon")
            if all(v is not None for v in (minlat, maxlat, minlon, maxlon)):
                mid_lat = (float(minlat) + float(maxlat)) / 2.0
                mid_lon = (float(minlon) + float(maxlon)) / 2.0
                if is_valid_coordinate(mid_lat, mid_lon):
                    return mid_lat, mid_lon
        except (ValueError, TypeError):
            pass

    return None


def parse_overpass_json(
    raw_data: Dict[str, Any],
    query_lat: float,
    query_lon: float,
    radius_km: float,
) -> Tuple[List[OsmFeature], Optional[NearestFeatureSummary]]:
    """
    Parse raw Overpass JSON response into normalized OsmFeature objects.

    Filters features within radius_km, deduplicates by osm_id, and sorts closest-first.
    Returns (features_list, nearest_industrial_summary).
    """
    elements = raw_data.get("elements", [])
    if not isinstance(elements, list):
        return [], None

    features: List[OsmFeature] = []
    seen_ids: set[str] = set()

    for elem in elements:
        if not isinstance(elem, dict):
            continue

        raw_id = elem.get("id")
        elem_type = elem.get("type", "node")
        if raw_id is None:
            continue

        osm_id = f"{elem_type}/{raw_id}"
        if osm_id in seen_ids:
            continue

        tags = elem.get("tags") or {}
        coords = extract_coordinates(elem)
        if coords is None:
            continue

        lat, lon = coords
        distance = haversine_km(query_lat, query_lon, lat, lon)
        if distance > radius_km:
            continue

        feature_type = classify_osm_feature_type(tags)
        name = tags.get("name") or tags.get("operator") or tags.get("brand")

        feature = OsmFeature(
            osmId=osm_id,
            osmType=elem_type,  # type: ignore[arg-type]
            featureType=feature_type,
            name=name,
            latitude=lat,
            longitude=lon,
            distanceKm=round(distance, 3),
            tags={str(k): str(v) for k, v in tags.items() if len(str(v)) <= 200},
        )

        seen_ids.add(osm_id)
        features.append(feature)

    # Sort closest first
    features.sort(key=lambda x: x.distance_km)

    # Find closest industrial feature
    nearest_summary: Optional[NearestFeatureSummary] = None
    if features:
        closest = features[0]
        nearest_summary = NearestFeatureSummary(
            name=closest.name,
            featureType=closest.feature_type,
            distanceKm=closest.distance_km,
            osmId=closest.osm_id,
        )

    return features, nearest_summary
