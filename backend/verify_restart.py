"""
Verify Persistence After Restart.
Checks that watches, alerts, reports, and observations survived the process restart.
"""

import requests

BASE_URL = "http://127.0.0.1:8787"


def main():
    print("=== Testing Persistence Across Restart ===")

    # 1. Check health
    res = requests.get(f"{BASE_URL}/api/v1/health")
    assert res.status_code == 200
    assert res.json()["database"] is True
    print("[OK] Health reports database: True")

    # 2. Check watches survived
    res = requests.get(f"{BASE_URL}/api/v1/watches")
    assert res.status_code == 200
    watches = res.json()
    assert len(watches) >= 1, "At least 1 watch site must survive restart"
    watch_names = [w["name"] for w in watches]
    print(f"[OK] {len(watches)} watches found after restart: {watch_names}")
    assert any("Live Verification Watch Site" in name for name in watch_names)

    # 3. Check alerts survived
    res = requests.get(f"{BASE_URL}/api/v1/alerts")
    assert res.status_code == 200
    alerts_data = res.json()
    assert alerts_data["total"] >= 1, "Alerts must survive restart"
    print(f"[OK] {alerts_data['total']} alerts found after restart")

    # 4. Check saved report survived
    res = requests.get(f"{BASE_URL}/api/v1/reports/live-report-1")
    assert res.status_code == 200, f"Saved report failed to load: {res.status_code}"
    rep = res.json()
    assert rep["id"] == "live-report-1"
    print(f"[OK] Saved report 'live-report-1' found after restart: classification='{rep['classification']}'")

    # 5. Check observations survived
    res = requests.get(f"{BASE_URL}/api/v1/observations?limit=10")
    assert res.status_code == 200
    obs = res.json()
    assert len(obs) >= 1, "Observations must survive restart"
    print(f"[OK] Observations found after restart: sample ID='{obs[0]['id']}'")

    print("\nALL PERSISTENCE-AFTER-RESTART VERIFICATIONS PASSED 100%!")


if __name__ == "__main__":
    main()
