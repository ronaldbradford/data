#!/usr/bin/env python
"""Export the most recent position of every vehicle as GeoJSON points.

Reads the Parquet position dataset built by translink_parquet.py and, for
each vehicle_id, keeps only its latest fix (by ts) as a Point feature —
ready to drop straight onto a map (Leaflet, kepler.gl, geojson.io, QGIS).

Requires: pip install duckdb

Examples:
    ./current_positions.py --out current.geojson
    ./current_positions.py --out current.geojson --region SEQ
    ./current_positions.py --out current.geojson --region SEQ --mode Bus
    ./current_positions.py --out current.geojson --max-age 300   # only vehicles seen in the last 5 min

Note: --mode only matches rows translink_parquet.py collected with that
same --mode — mode isn't part of the GTFS-RT payload, so rows collected
without --mode have no mode recorded and won't match a --mode filter here.
"""

import argparse
import sys

import duckdb

QUERY = """
INSTALL spatial; LOAD spatial;

COPY (
    WITH deduped AS (
        SELECT * EXCLUDE (rn) FROM (
            SELECT *, row_number() OVER (PARTITION BY vehicle_id, ts) AS rn
            FROM read_parquet('{glob}', hive_partitioning = true)
            WHERE lat IS NOT NULL {region_filter} {mode_filter}
        ) WHERE rn = 1
    ),
    latest AS (
        SELECT *,
               row_number() OVER (PARTITION BY vehicle_id ORDER BY ts DESC) AS rn2
        FROM deduped
    )
    SELECT
        vehicle_id, vehicle_label, trip_id, route_id,
        bearing, speed, current_status, occupancy_status,
        strftime(ts, '%Y-%m-%d %H:%M:%S') AS ts,
        ST_Point(lon, lat) AS geom
    FROM latest
    WHERE rn2 = 1 {age_filter}
) TO '{out_path}' WITH (FORMAT GDAL, DRIVER 'GeoJSON');
"""


def main():
    parser = argparse.ArgumentParser(
        description="Export each vehicle's most recent position as GeoJSON "
                     "points from the dataset built by translink_parquet.py.")
    parser.add_argument("--root", default="positions",
                        help="dataset root directory (default: positions)")
    parser.add_argument("--out", required=True, help="output .geojson path")
    parser.add_argument("--region", help="restrict to one region, e.g. SEQ "
                                          "(matches the hive region= partition)")
    parser.add_argument("--mode", help="restrict to one mode, e.g. Bus — only "
                                        "matches rows collected with that same "
                                        "--mode (see note above); most stored "
                                        "data has no mode recorded")
    parser.add_argument("--max-age", type=float,
                        help="drop vehicles whose latest fix is older than "
                             "this many seconds (default: no limit — the "
                             "true latest fix is kept even if stale)")
    args = parser.parse_args()

    glob = "%s/**/*.parquet" % args.root
    region_filter = " AND region = '%s'" % args.region if args.region else ""
    mode_filter = " AND mode = '%s'" % args.mode if args.mode else ""
    age_filter = (" AND ts >= now() - to_seconds(%d)" % args.max_age
                  if args.max_age else "")

    sql = QUERY.format(glob=glob, region_filter=region_filter,
                       mode_filter=mode_filter, age_filter=age_filter,
                       out_path=args.out)

    connection = duckdb.connect()
    connection.execute(sql)

    written = connection.execute(
        "SELECT count(*) FROM ST_Read('%s')" % args.out).fetchone()[0]
    print("%d vehicle(s) written to %s" % (written, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
