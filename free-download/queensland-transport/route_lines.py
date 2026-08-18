#!/usr/bin/env python
"""Export clean per-trip vehicle trajectories for one route as GeoJSON lines.

Reads the Parquet position dataset built by translink_parquet.py and draws
one LineString per contiguous run of fixes for each trip, using DuckDB's
spatial extension.

A naive "one line per trip_id" export produces spurious criss-crossing
lines: vehicles are sometimes tagged with the *next* trip_id while still
idle at the depot, minutes to over an hour before that trip actually
starts. Connecting that stray fix to the real trajectory draws one long
spurious segment across the map. This script avoids that by splitting each
trip wherever the gap between consecutive fixes exceeds --gap-threshold,
deduplicating exact (vehicle_id, ts) repeats first, and dropping segments
with too few points (--min-points) to be a real trip rather than a stray
fix or two.

Requires: pip install duckdb

Examples:
    ./route_lines.py 608 --out route608.geojson
    ./route_lines.py 608-5021 --exact --out route608-A.geojson
    ./route_lines.py 608 --out route608.geojson --gap-threshold 300 --min-points 10
"""

import argparse
import re
import sys

import duckdb

QUERY = """
INSTALL spatial; LOAD spatial;

COPY (
    WITH deduped AS (
        SELECT * EXCLUDE (rn) FROM (
            SELECT *, row_number() OVER (PARTITION BY vehicle_id, ts) AS rn
            FROM read_parquet('{glob}', hive_partitioning = true)
            WHERE {route_filter} AND lat IS NOT NULL
        ) WHERE rn = 1
    ),
    gapped AS (
        SELECT *,
               epoch(ts - lag(ts) OVER (PARTITION BY trip_id ORDER BY ts)) AS gap_s
        FROM deduped
    ),
    segmented AS (
        SELECT *,
               sum(CASE WHEN gap_s > {gap_threshold} THEN 1 ELSE 0 END)
                   OVER (PARTITION BY trip_id ORDER BY ts
                         ROWS UNBOUNDED PRECEDING)::INTEGER AS segment_id
        FROM gapped
    )
    SELECT trip_id, route_id,
           ST_MakeLine(list(ST_Point(lon, lat) ORDER BY ts)) AS geom
    FROM segmented
    GROUP BY trip_id, route_id, segment_id
    HAVING count(*) > {min_points}
) TO '{out_path}' WITH (FORMAT GDAL, DRIVER 'GeoJSON');
"""

ROUTE_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def main():
    parser = argparse.ArgumentParser(
        description="Export clean per-trip GeoJSON lines for one route from "
                     "the position dataset built by translink_parquet.py.")
    parser.add_argument("route", help="route prefix to match, e.g. 608 "
                                       "(matches split_part(route_id, '-', 1)); "
                                       "use --exact to match the full route_id")
    parser.add_argument("--exact", action="store_true",
                        help="match route_id exactly instead of its '-' prefix")
    parser.add_argument("--root", default="positions",
                        help="dataset root directory (default: positions)")
    parser.add_argument("--out", required=True, help="output .geojson path")
    parser.add_argument("--gap-threshold", type=float, default=180.0,
                        help="seconds between fixes beyond which a trip is "
                             "split into a new line (default: 180)")
    parser.add_argument("--min-points", type=int, default=5,
                        help="minimum fixes for a line segment to be kept "
                             "(default: 5)")
    args = parser.parse_args()

    if not ROUTE_RE.match(args.route):
        parser.error("route must contain only letters, digits, '-' and '_'")

    glob = "%s/**/*.parquet" % args.root
    if args.exact:
        route_filter = "route_id = '%s'" % args.route
    else:
        route_filter = "split_part(route_id, '-', 1) = '%s'" % args.route

    sql = QUERY.format(glob=glob, route_filter=route_filter,
                       gap_threshold=args.gap_threshold,
                       min_points=args.min_points, out_path=args.out)

    connection = duckdb.connect()
    connection.execute(sql)

    written = connection.execute(
        "SELECT count(*) FROM ST_Read('%s')" % args.out).fetchone()[0]
    print("%d line(s) written to %s" % (written, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
