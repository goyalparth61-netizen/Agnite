"""
Unit tests for OpenStreetMap Overpass response parser.
Tests coordinate extraction (node, way, relation, center, bounds),
tag categorization, radius filtering, deduplication, and nearest summary.
"""

import pytest
from app.providers.osm.parser import (
    classify_osm_feature_type,
    extract_coordinates,
    parse_overpass_json,
)


def test_classify_osm_feature_types():
    # 1. Thermal & emission structures
    assert classify_osm_feature_type({"man_made": "flare"}) == "flare"
    assert classify_osm_feature_type({"man_made": "chimney"}) == "chimney"

    # 2. Power infrastructure
    assert classify_osm_feature_type({"power": "plant"}) == "power_plant"
    assert classify_osm_feature_type({"name": "Koradi Thermal Power Station"}) == "power_plant"
    assert classify_osm_feature_type({"power": "substation"}) == "power_substation"

    # 3. Heavy industry sub-types
    assert classify_osm_feature_type({"industrial": "refinery"}) == "refinery"
    assert classify_osm_feature_type({"name": "Indian Oil Refinery"}) == "refinery"
    assert classify_osm_feature_type({"industrial": "steel"}) == "metal_works"
    assert classify_osm_feature_type({"name": "Tata Steel Foundry"}) == "metal_works"
    assert classify_osm_feature_type({"industrial": "chemical"}) == "chemical_plant"
    assert classify_osm_feature_type({"industrial": "cement"}) == "cement_works"

    # 4. General Works & Factories
    assert classify_osm_feature_type({"man_made": "works"}) == "factory"
    assert classify_osm_feature_type({"industrial": "manufacturing"}) == "factory"

    # 5. Industrial Landuse
    assert classify_osm_feature_type({"landuse": "industrial"}) == "industrial_area"

    # 6. Storage & Fuel
    assert classify_osm_feature_type({"man_made": "storage_tank"}) == "storage_tank"
    assert classify_osm_feature_type({"amenity": "fuel"}) == "fuel_infrastructure"

    # 7. Mining / Quarry
    assert classify_osm_feature_type({"landuse": "quarry"}) == "quarry"

    # 8. Unclassified
    assert classify_osm_feature_type({"building": "yes"}) == "industrial_other"


def test_extract_coordinates_node():
    elem = {"type": "node", "id": 101, "lat": 21.145, "lon": 79.088}
    coords = extract_coordinates(elem)
    assert coords is not None
    assert coords == (21.145, 79.088)


def test_extract_coordinates_way_center():
    # Ways with center from 'out center tags;'
    elem = {
        "type": "way",
        "id": 202,
        "center": {"lat": 21.150, "lon": 79.090},
    }
    coords = extract_coordinates(elem)
    assert coords is not None
    assert coords == (21.150, 79.090)


def test_extract_coordinates_relation_center():
    # Relations with center from 'out center tags;'
    elem = {
        "type": "relation",
        "id": 303,
        "center": {"lat": 21.160, "lon": 79.100},
    }
    coords = extract_coordinates(elem)
    assert coords is not None
    assert coords == (21.160, 79.100)


def test_extract_coordinates_bounds_fallback():
    elem = {
        "type": "way",
        "id": 404,
        "bounds": {
            "minlat": 21.10,
            "maxlat": 21.20,
            "minlon": 79.00,
            "maxlon": 79.10,
        },
    }
    coords = extract_coordinates(elem)
    assert coords is not None
    assert coords == (21.15, 79.05)


def test_extract_coordinates_missing_or_invalid():
    # Missing coordinates
    assert extract_coordinates({"type": "way", "id": 505}) is None
    # Invalid coordinates (out of range)
    assert extract_coordinates({"type": "node", "id": 506, "lat": 999.0, "lon": 79.0}) is None
    # Malformed types
    assert extract_coordinates({"type": "node", "id": 507, "lat": "not_a_number", "lon": 79.0}) is None


def test_parse_overpass_json_features_and_nearest():
    raw_overpass = {
        "elements": [
            {
                "type": "node",
                "id": 1,
                "lat": 21.147,
                "lon": 79.089,
                "tags": {"man_made": "flare", "name": "Refinery Flare Alpha"},
            },
            {
                "type": "way",
                "id": 2,
                "center": {"lat": 21.160, "lon": 79.095},
                "tags": {"power": "plant", "name": "Nagpur Power Station"},
            },
            {
                "type": "way",
                "id": 3,
                "center": {"lat": 22.000, "lon": 80.000},  # Far away (> 50 km)
                "tags": {"landuse": "industrial"},
            },
            {
                # Duplicate ID should be deduplicated
                "type": "node",
                "id": 1,
                "lat": 21.147,
                "lon": 79.089,
                "tags": {"man_made": "flare"},
            },
        ]
    }

    features, nearest = parse_overpass_json(
        raw_data=raw_overpass,
        query_lat=21.1466,
        query_lon=79.0889,
        radius_km=10.0,
    )

    # Only 2 features should be within 10 km (far feature excluded, duplicate excluded)
    assert len(features) == 2
    assert features[0].osm_id == "node/1"
    assert features[0].feature_type == "flare"
    assert features[0].name == "Refinery Flare Alpha"
    assert features[0].distance_km < 0.2  # ~50 meters

    assert features[1].osm_id == "way/2"
    assert features[1].feature_type == "power_plant"

    assert nearest is not None
    assert nearest.osm_id == "node/1"
    assert nearest.feature_type == "flare"
    assert nearest.name == "Refinery Flare Alpha"
