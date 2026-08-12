#!/usr/bin/env python
"""Poll Translink GTFS-Realtime vehicle positions into a SQLite database.

Builds a vehicle trajectory dataset: each row is one timestamped GPS fix for
one vehicle on one trip. Repeated polling of the feed accumulates the path a
vehicle takes from origin to destination.

Feed documentation: https://translink.com.au/about-translink/open-data/gtfs-rt
Data licensed CC-BY, State of Queensland. No authentication required.

Requires: pip install gtfs-realtime-bindings

Examples:
    # Single snapshot of all SEQ vehicles
    ./translink_poll.py --once

    # Poll SEQ buses every 20s for one hour
    ./translink_poll.py --mode Bus --interval 20 --max-runtime 3600

    # Show accumulated trip distances
    ./translink_poll.py --summary
"""

import argparse
import gzip
import io
import signal
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from math import asin, cos, radians, sin, sqrt

from google.transit import gtfs_realtime_pb2

FEED_BASE = "https://gtfsrt.api.translink.com.au/api/realtime"
REGIONS = ("SEQ", "CNS", "NSI", "MHB", "BOW")
MODES = ("Bus", "Rail", "Tram", "Ferry")
USER_AGENT = "translink-trajectory-collector/1.0"
EARTH_RADIUS_M = 6371008.8

SCHEMA = """
CREATE TABLE IF NOT EXISTS vehicle_position (
    vehicle_id       TEXT    NOT NULL,
    ts               INTEGER NOT NULL,
    region           TEXT    NOT NULL,
    vehicle_label    TEXT,
    trip_id          TEXT,
    route_id         TEXT,
    direction_id     INTEGER,
    start_date       TEXT,
    start_time       TEXT,
    lat              REAL,
    lon              REAL,
    bearing          REAL,
    speed            REAL,
    odometer         REAL,
    stop_id          TEXT,
    current_status   TEXT,
    occupancy_status TEXT,
    congestion_level TEXT,
    feed_ts          INTEGER,
    fetched_at       INTEGER NOT NULL,
    PRIMARY KEY (vehicle_id, ts)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS ix_vp_trip  ON vehicle_position (trip_id, ts);
CREATE INDEX IF NOT EXISTS ix_vp_route ON vehicle_position (route_id, ts);

CREATE TABLE IF NOT EXISTS poll_log (
    poll_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    fetched_at INTEGER NOT NULL,
    url        TEXT    NOT NULL,
    feed_ts    INTEGER,
    entities   INTEGER,
    inserted   INTEGER,
    bytes      INTEGER,
    status     TEXT
);
"""

INSERT_SQL = """
INSERT OR IGNORE INTO vehicle_position (
    vehicle_id, ts, region, vehicle_label, trip_id, route_id, direction_id,
    start_date, start_time, lat, lon, bearing, speed, odometer, stop_id,
    current_status, occupancy_status, congestion_level, feed_ts, fetched_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

SUMMARY_SQL = """
WITH stepped AS (
    SELECT
        trip_id,
        route_id,
        vehicle_id,
        ts,
        lat,
        lon,
        lag(lat) OVER w AS prev_lat,
        lag(lon) OVER w AS prev_lon,
        lag(ts)  OVER w AS prev_ts
    FROM vehicle_position
    WHERE trip_id IS NOT NULL
      AND lat IS NOT NULL
    WINDOW w AS (PARTITION BY trip_id, vehicle_id ORDER BY ts)
)
SELECT
    trip_id,
    route_id,
    vehicle_id,
    count(*)                                             AS points,
    datetime(min(ts), 'unixepoch', 'localtime')          AS first_fix,
    datetime(max(ts), 'unixepoch', 'localtime')          AS last_fix,
    round((max(ts) - min(ts)) / 60.0, 1)                 AS minutes,
    round(sum(haversine(prev_lat, prev_lon, lat, lon)) / 1000.0, 3) AS km,
    round(max(coalesce(haversine(prev_lat, prev_lon, lat, lon), 0)), 0) AS max_gap_m
FROM stepped
GROUP BY trip_id, route_id, vehicle_id
HAVING points > 1
ORDER BY km DESC
LIMIT ?
"""


class Stopped(Exception):
    """Raised when a shutdown signal is received."""


def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in metres. Returns None if any input is NULL."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = phi2 - phi1
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(sqrt(a))


def feed_url(region, mode=None):
    """Build a VehiclePositions endpoint URL."""
    url = "%s/%s/VehiclePositions" % (FEED_BASE, region)
    if mode:
        url = "%s/%s" % (url, mode)
    return url


def fetch(url, etag=None, timeout=30):
    """Fetch the protobuf payload. Returns (payload, etag); payload is None on 304."""
    request = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip",
    })
    if etag:
        request.add_header("If-None-Match", etag)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
            if response.headers.get("Content-Encoding") == "gzip":
                payload = gzip.GzipFile(fileobj=io.BytesIO(payload)).read()
            return payload, response.headers.get("ETag")
    except urllib.error.HTTPError as error:
        if error.code == 304:
            return None, etag
        raise


def enum_name(descriptor, value):
    """Map a protobuf enum value to its symbolic name, tolerating unknowns."""
    try:
        return descriptor.Name(value)
    except ValueError:
        return str(value)


def parse_feed(payload, region, fetched_at):
    """Decode a FeedMessage into insertable rows."""
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(payload)
    feed_ts = feed.header.timestamp or None
    rows = []

    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue
        vehicle = entity.vehicle
        descriptor = vehicle.vehicle
        trip = vehicle.trip
        position = vehicle.position

        vehicle_id = descriptor.id or entity.id
        if not vehicle_id:
            continue

        # A vehicle timestamp of 0 means the operator did not supply one;
        # fall back to the feed header so the primary key stays meaningful.
        ts = vehicle.timestamp or feed_ts or fetched_at

        rows.append((
            vehicle_id,
            ts,
            region,
            descriptor.label or None,
            trip.trip_id or None,
            trip.route_id or None,
            trip.direction_id if trip.HasField("direction_id") else None,
            trip.start_date or None,
            trip.start_time or None,
            position.latitude if position.HasField("latitude") else None,
            position.longitude if position.HasField("longitude") else None,
            position.bearing if position.HasField("bearing") else None,
            position.speed if position.HasField("speed") else None,
            position.odometer if position.HasField("odometer") else None,
            vehicle.stop_id or None,
            enum_name(gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus,
                      vehicle.current_status),
            enum_name(gtfs_realtime_pb2.VehiclePosition.OccupancyStatus,
                      vehicle.occupancy_status),
            enum_name(gtfs_realtime_pb2.VehiclePosition.CongestionLevel,
                      vehicle.congestion_level),
            feed_ts,
            fetched_at,
        ))

    return feed_ts, rows


def connect(path):
    """Open the database, apply the schema and register helper functions."""
    connection = sqlite3.connect(path)
    connection.executescript(SCHEMA)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.create_function("haversine", 4, haversine, deterministic=True)
    return connection


def poll_once(connection, url, region, etag, verbose=False):
    """Fetch, parse and store one snapshot. Returns the new ETag."""
    fetched_at = int(time.time())
    try:
        payload, new_etag = fetch(url, etag)
    except (urllib.error.URLError, TimeoutError) as error:
        connection.execute(
            "INSERT INTO poll_log (fetched_at, url, feed_ts, entities, inserted, "
            "bytes, status) VALUES (?, ?, NULL, NULL, NULL, NULL, ?)",
            (fetched_at, url, "error: %s" % error))
        connection.commit()
        print("fetch failed: %s" % error, file=sys.stderr)
        return etag

    if payload is None:
        if verbose:
            print("feed unchanged (304)")
        return new_etag

    feed_ts, rows = parse_feed(payload, region, fetched_at)
    cursor = connection.executemany(INSERT_SQL, rows)
    inserted = cursor.rowcount
    connection.execute(
        "INSERT INTO poll_log (fetched_at, url, feed_ts, entities, inserted, "
        "bytes, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (fetched_at, url, feed_ts, len(rows), inserted, len(payload), "ok"))
    connection.commit()

    print("%s  entities=%-5d new=%-5d bytes=%d" % (
        time.strftime("%H:%M:%S", time.localtime(fetched_at)),
        len(rows), inserted, len(payload)))
    return new_etag


def run_summary(connection, limit):
    """Print per-trip trajectory statistics derived from stored fixes."""
    rows = connection.execute(SUMMARY_SQL, (limit,)).fetchall()
    if not rows:
        print("No multi-point trips stored yet. Poll for a few minutes first.")
        return

    header = ("trip_id", "route", "vehicle", "pts", "first fix", "last fix",
              "mins", "km", "max gap m")
    print("%-24s %-8s %-12s %5s %-19s %-19s %6s %8s %9s" % header)
    for row in rows:
        print("%-24s %-8s %-12s %5d %-19s %-19s %6s %8s %9s" % tuple(
            "" if value is None else value for value in row))


def main():
    parser = argparse.ArgumentParser(
        description="Collect Translink GTFS-RT vehicle positions into SQLite.")
    parser.add_argument("--region", default="SEQ", choices=REGIONS,
                        help="Translink region feed (default: SEQ)")
    parser.add_argument("--mode", choices=MODES,
                        help="restrict to one mode; SEQ only")
    parser.add_argument("--db", default="translink.db",
                        help="SQLite database path (default: translink.db)")
    parser.add_argument("--interval", type=float, default=20.0,
                        help="seconds between polls (default: 20)")
    parser.add_argument("--max-runtime", type=float,
                        help="stop after this many seconds")
    parser.add_argument("--once", action="store_true",
                        help="take a single snapshot and exit")
    parser.add_argument("--summary", action="store_true",
                        help="print trip distances from stored data and exit")
    parser.add_argument("--limit", type=int, default=20,
                        help="rows to show with --summary (default: 20)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.mode and args.region != "SEQ":
        parser.error("mode-specific feeds are only published for SEQ")
    if args.interval < 5:
        parser.error("interval below 5s is impolite; the feed updates slower than that")

    connection = connect(args.db)

    if args.summary:
        run_summary(connection, args.limit)
        connection.close()
        return 0

    url = feed_url(args.region, args.mode)
    print("polling %s every %.0fs -> %s" % (url, args.interval, args.db))

    def stop(signum, frame):
        raise Stopped()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    started = time.monotonic()
    etag = None
    try:
        while True:
            etag = poll_once(connection, url, args.region, etag, args.verbose)
            if args.once:
                break
            if args.max_runtime and time.monotonic() - started >= args.max_runtime:
                break
            time.sleep(args.interval)
    except Stopped:
        print("\nstopping")
    finally:
        total = connection.execute(
            "SELECT count(*) FROM vehicle_position").fetchone()[0]
        print("%d position rows stored in %s" % (total, args.db))
        connection.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
