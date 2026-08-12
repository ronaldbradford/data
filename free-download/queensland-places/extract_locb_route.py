#!/usr/bin/env python3
"""
Extract random samples of 'Bounded locality' (LOCB) places from the
Queensland place names gazetteer CSV, then build a GeoJSON LineString
connecting them in nearest-neighbour order (starting from the first
selected point, always hopping to the closest unvisited point next).

With --iterations N, the sample-and-route process is repeated N times
and all resulting routes are written into a single GeoJSON file as
separate LineString features (one route per iteration).

Usage:
    python3 extract_locb_route.py [--count N] [--iterations N] [--seed S] [--input FILE] [--output FILE]

    --count N       Number of locations per route, 3-6 (default: random in that range each iteration)
    --iterations N  Number of routes to generate into the one output file (default: 1)
    --seed S        Random seed for reproducibility (optional)
    --input FILE    Source CSV (default: queensland.csv)
    --output FILE   Output GeoJSON file (default: locb_route.geojson)
"""

import argparse
import csv
import json
import math
import random
import sys


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two lat/lon points, in kilometres."""
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_locb_rows(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("type") != "LOCB":
                continue
            try:
                lat = float(row["latitude_dd"])
                lon = float(row["longitude_dd"])
            except (TypeError, ValueError):
                continue
            rows.append(
                {
                    "reference_number": row.get("reference_number"),
                    "place_name": row.get("place_name"),
                    "lga_name": row.get("lga_name"),
                    "lat": lat,
                    "lon": lon,
                }
            )
    return rows


def nearest_neighbour_order(points):
    """Order points starting at points[0], always visiting the nearest
    remaining point next (a simple nearest-neighbour path, not a full TSP)."""
    remaining = points[1:]
    ordered = [points[0]]
    current = points[0]
    while remaining:
        nxt = min(remaining, key=lambda p: haversine_km(current["lat"], current["lon"], p["lat"], p["lon"]))
        ordered.append(nxt)
        remaining.remove(nxt)
        current = nxt
    return ordered


def route_features(ordered_points, iteration):
    """Build the LineString feature plus per-point Point features for a
    single route, tagged with its iteration number."""
    coords = [[p["lon"], p["lat"]] for p in ordered_points]

    line_feature = {
        "type": "Feature",
        "properties": {
            "name": f"Bounded locality route {iteration}",
            "iteration": iteration,
            "point_count": len(ordered_points),
            "order": [p["place_name"] for p in ordered_points],
        },
        "geometry": {
            "type": "LineString",
            "coordinates": coords,
        },
    }

    point_features = [
        {
            "type": "Feature",
            "properties": {
                "iteration": iteration,
                "reference_number": p["reference_number"],
                "place_name": p["place_name"],
                "lga_name": p["lga_name"],
                "sequence": i + 1,
            },
            "geometry": {
                "type": "Point",
                "coordinates": [p["lon"], p["lat"]],
            },
        }
        for i, p in enumerate(ordered_points)
    ]

    return [line_feature] + point_features


def build_geojson(routes):
    """routes: list of ordered_points lists, one per iteration."""
    features = []
    for i, ordered_points in enumerate(routes, 1):
        features.extend(route_features(ordered_points, i))

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=None, help="Number of locations per route (3-6)")
    parser.add_argument("--iterations", type=int, default=1, help="Number of routes to generate (default: 1)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--input", default="queensland.csv", help="Source CSV file")
    parser.add_argument("--output", default="locb_route.geojson", help="Output GeoJSON file")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if args.count is not None and not (3 <= args.count <= 6):
        sys.exit("--count must be between 3 and 6")

    if args.iterations < 1:
        sys.exit("--iterations must be at least 1")

    rows = load_locb_rows(args.input)
    min_needed = args.count if args.count is not None else 3
    if len(rows) < min_needed:
        sys.exit(f"Only {len(rows)} LOCB rows with coordinates found; need at least {min_needed}")

    routes = []
    for iteration in range(1, args.iterations + 1):
        count = args.count if args.count is not None else random.randint(3, 6)
        selected = random.sample(rows, count)
        ordered = nearest_neighbour_order(selected)
        routes.append(ordered)

        print(f"Route {iteration} - {count} bounded localities:")
        for i, p in enumerate(ordered, 1):
            print(f"  {i}. {p['place_name']} ({p['lat']:.5f}, {p['lon']:.5f}) - {p['lga_name']}")

    geojson = build_geojson(routes)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2)

    print(f"\n{len(routes)} route(s) written to {args.output}")


if __name__ == "__main__":
    main()
