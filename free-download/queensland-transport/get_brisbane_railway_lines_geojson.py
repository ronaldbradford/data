#!/usr/bin/env python
"""
Download Brisbane / South East Queensland railway line locations as GeoJSON
from Brisbane City Council's Open Data portal (Opendatasoft platform).

Dataset: "Railway — Line locations"
Coverage: SEQ railway centrelines, roughly Gympie (north) to Toowoomba (west)
          to the NSW border (south) — i.e. the full Queensland Rail Citytrain
          network including Brisbane's suburban lines, not just the CBD.
Source:   https://data.brisbane.qld.gov.au/explore/dataset/railway-line-locations/
Licence:  Creative Commons Attribution 4.0 (Brisbane City Council)

Usage:
    python get_brisbane_railway_lines_geojson.py
    python get_brisbane_railway_lines_geojson.py --out brisbane_rail.geojson
"""

import argparse
import json
import sys
import urllib.request

DATASET_ID = "railway-line-locations"
EXPORT_URL = (
    f"https://data.brisbane.qld.gov.au/api/explore/v2.1/catalog/"
    f"datasets/{DATASET_ID}/exports/geojson?limit=-1"
)


def fetch_geojson(timeout: int = 60) -> dict:
    req = urllib.request.Request(EXPORT_URL, headers={"User-Agent": "python-urllib"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download Brisbane/SEQ railway line locations as GeoJSON"
    )
    parser.add_argument(
        "--out",
        default="brisbane_railway_lines.geojson",
        help="Output file path (default: brisbane_railway_lines.geojson)",
    )
    args = parser.parse_args()

    print("Fetching railway line locations...", file=sys.stderr)
    try:
        geojson = fetch_geojson()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    features = geojson.get("features", [])
    if not features:
        print("No features returned — dataset may have moved or changed.", file=sys.stderr)
        sys.exit(1)

    with open(args.out, "w") as f:
        json.dump(geojson, f)

    print(f"Saved {len(features)} feature(s) -> {args.out}", file=sys.stderr)
    print(
        "Source: Brisbane City Council Open Data, licensed CC BY 4.0. "
        "Attribution required in derived products.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
