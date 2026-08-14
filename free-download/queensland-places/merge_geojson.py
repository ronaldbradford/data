#!/usr/bin/env python3
"""
Combine multiple GeoJSON files into a single FeatureCollection.

Each input file may itself be a FeatureCollection, a single Feature, or a
bare geometry object - all are normalised to Features and concatenated into
one output FeatureCollection, in the order the input files are given.

Usage:
    python3 merge_geojson.py <destination.geojson> <file1.geojson> <file2.geojson> [...]

    destination.geojson  Output file to write (overwritten if it exists)
    file...               Two or more input GeoJSON files to combine

    --source-property NAME  Record each feature's source filename in
                             properties[NAME] (optional)
"""

import argparse
import json
import sys


def load_features(path):
    """Read a GeoJSON file and return a list of Feature objects, whatever
    the top-level type (FeatureCollection, Feature, or bare geometry)."""
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)

    gtype = data.get("type")
    if gtype == "FeatureCollection":
        features = data.get("features", [])
    elif gtype == "Feature":
        features = [data]
    elif gtype in (
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
        "GeometryCollection",
    ):
        features = [{"type": "Feature", "properties": {}, "geometry": data}]
    else:
        sys.exit(f"{path}: unrecognised GeoJSON type {gtype!r}")

    return features


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("destination", help="Output GeoJSON file")
    parser.add_argument("sources", nargs="+", help="Input GeoJSON files to combine")
    parser.add_argument(
        "--source-property",
        default=None,
        help="Record each feature's source filename in properties[NAME]",
    )
    args = parser.parse_args()

    features = []
    for path in args.sources:
        file_features = load_features(path)
        if args.source_property:
            for feature in file_features:
                feature.setdefault("properties", {})
                if feature["properties"] is None:
                    feature["properties"] = {}
                feature["properties"][args.source_property] = path
        features.extend(file_features)
        print(f"{path}: {len(file_features)} feature(s)")

    combined = {
        "type": "FeatureCollection",
        "features": features,
    }

    with open(args.destination, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)

    print(f"\n{len(features)} feature(s) from {len(args.sources)} file(s) written to {args.destination}")


if __name__ == "__main__":
    main()
