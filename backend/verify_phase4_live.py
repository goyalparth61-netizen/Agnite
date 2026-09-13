"""
Live Verification Script for AGNITE Phase 4.
Executes live operations against FastAPI running on port 8787.
"""

from __future__ import annotations

import json
import time
import requests

BASE_URL = "http://127.0.0.1:8787"


def main():
    print("=== Step 1: Health and Database Connectivity ===")
    res = requests.get(f"{BASE_URL}/api/v1/health")
    assert res.status_code == 200, f"Health check failed: {res.status_code}"
    health_data = res.json()
    print("Health response:", health_data)
    assert health_data.get("database") is True, "Database should report True"

    print("\n=== Step 2 & 3: Load FIRMS Feed & Confirm Persistence ===")
    res = requests.get(f"{BASE_URL}/api/firms?sensor=noaa20&hours=24")
    assert res.status_code == 200, f"FIRMS fetch failed: {res.status_code}"
    feed_data = res.json()
    obs_count = len(feed_data.get("observations", []))
    print(f"FIRMS feed returned {obs_count} observations (sensor: {feed_data.get('sensor')})")

    # Give async persistence task a brief moment to finish
    time.sleep(1.0)

    res = requests.get(f"{BASE_URL}/api/v1/observations?limit=500")
    assert res.status_code == 200
    stored_obs = res.json()
    stored_count_1 = len(stored_obs)
    print(f"Persisted observations count in DB: {stored_count_1}")
    assert stored_count_1 > 0, "Observations should be persisted in database"

    print("\n=== Step 4 & 5: Refresh Same Feed & Confirm Zero Duplicate Growth ===")
    res = requests.get(f"{BASE_URL}/api/firms?sensor=noaa20&hours=24")
    assert res.status_code == 200
    time.sleep(0.5)

    res = requests.get(f"{BASE_URL}/api/v1/observations?limit=500")
    stored_count_2 = len(res.json())
    print(f"Persisted observations after re-fetching feed: {stored_count_2}")
    assert stored_count_2 == stored_count_1, "Duplicate observations must NOT be created on feed refresh"

    print("\n=== Step 6, 7 & 8: Select Hotspot & Run Analysis with History ===")
    selected = feed_data["observations"][0]
    print(f"Selected hotspot: ID {selected['id']} at ({selected['latitude']}, {selected['longitude']}), FRP {selected['frp']} MW")

    analysis_payload = {
        "selectedObservation": selected,
        "observations": [selected],  # Only 1 observation sent from frontend
        "radiusKm": 5.0,
    }
    res = requests.post(f"{BASE_URL}/api/v1/analysis/run", json=analysis_payload)
    assert res.status_code == 200, f"Analysis failed: {res.text}"
    analysis = res.json()
    print(f"Analysis Result: Classification='{analysis['classification']}', Risk={analysis['risk']['index']} ({analysis['risk']['level']})")
    print(f"Statistics: Included={analysis['statistics']['included']}, DistinctTimes={analysis['statistics']['distinctTimes']}")

    print("\n=== Step 9: Create Watch Site ===")
    watch_payload = {
        "name": "Live Verification Watch Site",
        "latitude": selected["latitude"],
        "longitude": selected["longitude"],
        "radiusKm": 5.0,
        "frpThreshold": min(10.0, selected["frp"] * 0.8),  # Threshold below hotspot FRP so alert triggers
        "riskThreshold": 30,
    }
    res = requests.post(f"{BASE_URL}/api/v1/watches", json=watch_payload)
    assert res.status_code == 201, f"Watch creation failed: {res.text}"
    created_watch = res.json()
    watch_id = created_watch["id"]
    print(f"Created Watch: ID {watch_id}, Name='{created_watch['name']}', Threshold={created_watch['frpThreshold']} MW")

    print("\n=== Step 10 & 11: Run Watch Scanner & Verify Alert Generation ===")
    from app.jobs.watch_scanner import run_watch_scanner
    scanner_result = run_watch_scanner()
    print("Scanner summary:", scanner_result)
    assert scanner_result["alerts_generated"] >= 1, "Expected at least 1 alert to be generated"

    res = requests.get(f"{BASE_URL}/api/v1/alerts?watchId={watch_id}")
    assert res.status_code == 200
    alerts_data = res.json()
    print(f"Alerts for watch {watch_id}: total={alerts_data['total']}")
    assert alerts_data["total"] >= 1, "Alert should be present in alert list"
    alert = alerts_data["alerts"][0]
    print(f"Latest alert: [{alert['severity']}] {alert['title']} — {alert['message']}")

    print("\n=== Step 12 & 13: Run Scanner Again & Verify Zero Duplicate Alerts ===")
    scanner_result_2 = run_watch_scanner()
    print("Second scanner summary:", scanner_result_2)
    assert scanner_result_2["alerts_generated"] == 0, "Second scan must generate 0 duplicate alerts"

    res = requests.get(f"{BASE_URL}/api/v1/alerts?watchId={watch_id}")
    alerts_data_2 = res.json()
    assert alerts_data_2["total"] == alerts_data["total"], "Alert count must remain identical"
    print("Alert count verified identical:", alerts_data_2["total"])

    print("\n=== Step 14 & 15: Save Analysis Report & Retrieve from Backend ===")
    report_payload = {
        "id": "live-report-1",
        "label": f"{selected['latitude']}, {selected['longitude']}",
        "latitude": selected["latitude"],
        "longitude": selected["longitude"],
        "classification": analysis["classification"],
        "confidence": analysis.get("confidence", 85.0),
        "risk": analysis["risk"]["index"],
        "summary": analysis["summary"],
        "report": analysis,
        "context": {"landCover": "industrial"},
        "observations": [selected],
    }
    res = requests.post(f"{BASE_URL}/api/v1/reports", json=report_payload)
    assert res.status_code == 201, f"Report save failed: {res.text}"
    saved_report = res.json()
    print(f"Saved Report: ID {saved_report['id']}, Classification='{saved_report['classification']}', Label='{saved_report['label']}'")

    res = requests.get(f"{BASE_URL}/api/v1/reports/live-report-1")
    assert res.status_code == 200
    retrieved_report = res.json()
    assert retrieved_report["id"] == "live-report-1"
    print("Successfully retrieved saved report by ID:", retrieved_report["id"])

    print("\n=== Phase 4 Live Verification: Part 1 Complete! ===")
    print("Proceed to restart test...")


if __name__ == "__main__":
    main()
