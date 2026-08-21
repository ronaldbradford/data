#!/usr/bin/env python
"""
Build a styled GeoJSON of NYC subway service lines:
  - LineString features colored with the official MTA line color
  - Point features marking the two endpoints of each line, labeled with
    the line identifier (for use as map markers)

Data sources (New York State Open Data / Socrata, data.ny.gov):
  - "MTA Subway Service Lines" (s692-irgq) -- line geometries
  - "MTA Colors" (3uhz-sej2) -- official RGB hex / CMYK per service

Usage:
    python get_nyc_subway_lines_styled_geojson.py
    python get_nyc_subway_lines_styled_geojson.py --out nyc_subway_styled.geojson
    python get_nyc_subway_lines_styled_geojson.py "L"   # single line only
"""

import argparse
import json
import math
import re
import sys
import urllib.request

LINES_DATASET_ID = "s692-irgq"
COLORS_DATASET_ID = "3uhz-sej2"
PAGE_SIZE = 1000

CANDIDATE_LINE_FIELDS = [
    "route_id", "line", "name", "service", "rt_symbol", "label", "route",
]

# Candidate field names for the color dataset -- probed at runtime since the
# exact schema (e.g. "service", "line", "hex", "rgb_hex") isn't confirmed.
CANDIDATE_COLOR_NAME_FIELDS = ["service", "line", "route", "name", "label"]
CANDIDATE_COLOR_HEX_FIELDS = ["hex_color", "hex", "rgb_hex", "hex_code", "color_hex", "rgb"]


def http_get_json(url: str, timeout: int = 60) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "python-urllib"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_all_geojson_features(dataset_id: str, timeout: int = 60) -> list:
    features = []
    offset = 0
    while True:
        url = (
            f"https://data.ny.gov/resource/{dataset_id}.geojson"
            f"?$limit={PAGE_SIZE}&$offset={offset}"
        )
        page = http_get_json(url, timeout=timeout)
        page_features = page.get("features", [])
        if not page_features:
            break
        features.extend(page_features)
        if len(page_features) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return features


def fetch_all_json_rows(dataset_id: str, timeout: int = 60) -> list:
    rows = []
    offset = 0
    while True:
        url = f"https://data.ny.gov/resource/{dataset_id}.json?$limit={PAGE_SIZE}&$offset={offset}"
        page_rows = http_get_json(url, timeout=timeout)
        if not page_rows:
            break
        rows.extend(page_rows)
        if len(page_rows) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def detect_field(sample: dict, candidates: list, kind: str) -> str:
    for field in candidates:
        if field in sample:
            return field
    raise RuntimeError(
        f"Could not auto-detect the {kind} field. Available properties: {list(sample.keys())}"
    )


def build_color_lookup(color_rows: list) -> dict:
    """Map the raw (uppercased) service/name string -> '#RRGGBB' hex string.

    Kept un-split, since MTA Colors groups trunk lines into one entry (e.g.
    'A C E' or '4 5 6'). Matching against these happens later via regex in
    match_line_color(), which looks for the target line as a whole token.
    """
    if not color_rows:
        return {}

    name_field = detect_field(color_rows[0], CANDIDATE_COLOR_NAME_FIELDS, "color-name")
    hex_field = detect_field(color_rows[0], CANDIDATE_COLOR_HEX_FIELDS, "color-hex")

    print(f"  raw color rows (field '{name_field}' -> '{hex_field}'):", file=sys.stderr)
    for row in color_rows:
        print(f"    {row.get(name_field)!r} -> {row.get(hex_field)!r}", file=sys.stderr)

    lookup = {}
    for row in color_rows:
        name = str(row.get(name_field, "")).strip().upper()
        hexval = str(row.get(hex_field, "")).strip()
        if not name or not hexval:
            continue
        if not hexval.startswith("#"):
            hexval = f"#{hexval}"
        lookup[name] = hexval
    return lookup


def match_line_color(line_name: str, color_lookup: dict):
    """
    Find a color whose (grouped) name entry contains the target line as a
    whole token -- bounded by string start/end or a separator character
    (space, comma, slash, hyphen). E.g. target '7' matches key '7' or
    '7 EXPRESS', but not '17' or 'B7'. Target 'A' matches 'A C E'.
    """
    target = re.escape(line_name.strip().upper())
    pattern = re.compile(rf"(?:^|[\s,/()-]){target}(?:$|[\s,/()-])")
    for key, hexval in color_lookup.items():
        if pattern.search(key):
            return hexval
    return None


def haversine(lon1, lat1, lon2, lat2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def flatten_coords(geom: dict) -> list:
    """Return a flat list of [lon, lat] pairs for LineString/MultiLineString."""
    gtype = geom.get("type")
    if gtype == "LineString":
        return geom.get("coordinates", [])
    if gtype == "MultiLineString":
        pts = []
        for part in geom.get("coordinates", []):
            pts.extend(part)
        return pts
    return []


def find_endpoints(geom: dict):
    """
    Return the two most-distant points along the line's vertex sequence
    (first and last vertex of the overall path -- true geometric endpoints
    of the line as drawn, not just extreme lat/lon).
    """
    coords = flatten_coords(geom)
    if len(coords) < 2:
        return None, None
    return coords[0], coords[-1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build styled NYC subway GeoJSON with line colors and endpoint markers"
    )
    parser.add_argument(
        "line", nargs="?", default=None,
        help="Optional single line identifier (e.g. 'L') to restrict output to.",
    )
    parser.add_argument(
        "--out", default=None,
        help="Output file path (default: nyc_subway_lines_styled.geojson, or "
        "nyc_subway_line_<LINE>_styled.geojson when a line is given)",
    )
    args = parser.parse_args()

    print("Fetching line geometries...", file=sys.stderr)
    line_features = fetch_all_geojson_features(LINES_DATASET_ID)
    if not line_features:
        print("ERROR: no line features returned.", file=sys.stderr)
        sys.exit(1)

    line_field = detect_field(line_features[0].get("properties", {}), CANDIDATE_LINE_FIELDS, "line-name")
    print(f"  using '{line_field}' as the line identifier field", file=sys.stderr)

    print("Fetching official MTA colors...", file=sys.stderr)
    try:
        color_rows = fetch_all_json_rows(COLORS_DATASET_ID)
        color_lookup = build_color_lookup(color_rows)
        print(f"  loaded {len(color_lookup)} color entries", file=sys.stderr)
        print("  color entries found:", file=sys.stderr)
        for k, v in sorted(color_lookup.items()):
            print(f"    {k!r} -> {v}", file=sys.stderr)
    except Exception as exc:
        print(f"  WARNING: could not load MTA Colors dataset ({exc}); "
              f"lines will be output without a matched color.", file=sys.stderr)
        color_lookup = {}

    if args.line:
        target = args.line.strip().upper()
        line_features = [
            f for f in line_features
            if str(f.get("properties", {}).get(line_field, "")).strip().upper() == target
        ]
        if not line_features:
            print(f"No features matched '{args.line}' on field '{line_field}'.", file=sys.stderr)
            sys.exit(1)

    out_features = []
    unmatched_colors = set()

    for feat in line_features:
        props = feat.get("properties", {})
        name = str(props.get(line_field, "")).strip()
        geom = feat.get("geometry", {})

        color = match_line_color(name, color_lookup)
        if color is None:
            unmatched_colors.add(name)

        props = dict(props)
        props["stroke"] = color or "#808080"
        props["stroke-width"] = 4
        props["stroke-opacity"] = 1
        out_features.append({
            "type": "Feature",
            "properties": props,
            "geometry": geom,
        })

        start, end = find_endpoints(geom)
        for pt, suffix in ((start, "start"), (end, "end")):
            if pt is None:
                continue
            out_features.append({
                "type": "Feature",
                "properties": {
                    "marker-symbol": name,
                    "label": name,
                    "line": name,
                    "endpoint": suffix,
                    "marker-color": color or "#808080",
                },
                "geometry": {"type": "Point", "coordinates": pt},
            })

    if unmatched_colors:
        print(
            f"  NOTE: no color match found for {len(unmatched_colors)} line value(s), "
            f"defaulted to gray: {sorted(unmatched_colors)}",
            file=sys.stderr,
        )

    geojson = {"type": "FeatureCollection", "features": out_features}

    if args.line:
        out_path = args.out or f"nyc_subway_line_{args.line.replace('/', '-')}_styled.geojson"
    else:
        out_path = args.out or "nyc_subway_lines_styled.geojson"

    with open(out_path, "w") as f:
        json.dump(geojson, f)

    n_lines = sum(1 for f in out_features if f["geometry"]["type"] != "Point")
    n_markers = sum(1 for f in out_features if f["geometry"]["type"] == "Point")
    print(f"\nSaved {n_lines} line feature(s) and {n_markers} endpoint marker(s) -> {out_path}",
          file=sys.stderr)
    print(
        "Sources: MTA Subway Service Lines & MTA Colors, New York State Open Data "
        "(data.ny.gov). See dataset pages for licensing terms.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
