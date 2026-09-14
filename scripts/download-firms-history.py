"""Download historical India-region NASA FIRMS CSV chunks for model training.

Requires a free NASA FIRMS MAP_KEY in the environment:
  PowerShell: $env:NASA_FIRMS_MAP_KEY="..."

Example:
  python scripts/download-firms-history.py --start 2025-01-01 --end 2025-12-31

The key is never written to disk or printed. FIRMS Area API supports at most a
small multi-day range per request, so the script downloads five-day chunks.
Prefer Standard Processing (SP) data for model development when available.
"""

from __future__ import annotations

import argparse
import os
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

AREA = "67,6,99,38"
BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
SUPPORTED = {
    "VIIRS_NOAA20_SP",
    "VIIRS_SNPP_SP",
    "MODIS_SP",
    "VIIRS_NOAA20_NRT",
    "VIIRS_NOAA21_NRT",
    "VIIRS_SNPP_NRT",
    "MODIS_NRT",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD, inclusive")
    parser.add_argument("--source", default="VIIRS_NOAA20_SP", choices=sorted(SUPPORTED))
    parser.add_argument("--output-dir", default="data/firms")
    parser.add_argument("--pause", type=float, default=0.25, help="seconds between requests")
    return parser.parse_args()


def parse_day(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def main() -> None:
    args = parse_args()
    key = os.environ.get("NASA_FIRMS_MAP_KEY", "").strip()
    if not key:
        raise SystemExit("NASA_FIRMS_MAP_KEY is required. Request a free key from NASA FIRMS and set it in your shell.")
    start = parse_day(args.start)
    end = parse_day(args.end)
    if end < start:
        raise SystemExit("--end must be on or after --start")
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    current = start
    downloaded = 0
    while current <= end:
        remaining = (end - current).days + 1
        days = min(5, remaining)
        target = output / f"{args.source}_{current.isoformat()}_{days}d.csv"
        if target.exists() and target.stat().st_size > 50:
            print(f"skip {target.name}")
            current += timedelta(days=days)
            continue
        url = f"{BASE}/{key}/{args.source}/{AREA}/{days}/{current.isoformat()}"
        request = urllib.request.Request(
            url,
            headers={"Accept": "text/csv", "User-Agent": "AGNITE-SIH26162/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read()
        except urllib.error.HTTPError as error:
            raise SystemExit(f"FIRMS request failed with HTTP {error.code} for {current.isoformat()}") from error
        except urllib.error.URLError as error:
            raise SystemExit(f"FIRMS request failed for {current.isoformat()}: {error.reason}") from error
        if len(body) < 20 or b"latitude" not in body[:500].lower():
            raise SystemExit(f"Unexpected FIRMS response for {current.isoformat()}; file was not saved.")
        target.write_bytes(body)
        print(f"saved {target.name} ({len(body):,} bytes)")
        downloaded += 1
        current += timedelta(days=days)
        if current <= end:
            time.sleep(max(0.0, args.pause))
    print(f"Complete: {downloaded} new files in {output}")
    print("Next: python scripts/train-firms-recurrence-model.py data/firms/*.csv")


if __name__ == "__main__":
    main()
