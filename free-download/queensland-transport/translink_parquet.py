#!/usr/bin/env python
"""Poll Translink GTFS-Realtime vehicle positions into a partitioned Parquet dataset.

Each row is one timestamped GPS fix for one vehicle on one trip. Repeated
polling accumulates the path a vehicle takes from origin to destination.

Output is a Hive-partitioned directory that DuckDB reads directly:

    positions/dt=2026-08-11/region=SEQ/part-1786434892-31337-0003.parquet

Files are written atomically (temp name, then rename), so a reader scanning the
directory never sees a half-written file.

Feed documentation: https://translink.com.au/about-translink/open-data/gtfs-rt
Data licensed CC-BY, State of Queensland. No authentication required.

Requires: pip install gtfs-realtime-bindings pyarrow

Examples:
    ./translink_parquet.py --once
    ./translink_parquet.py --mode Bus --interval 20 --max-runtime 86400
    ./translink_parquet.py --summary          # needs duckdb installed
"""

import argparse
import gzip
import io
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

import pyarrow as pa
import pyarrow.parquet as pq
from google.transit import gtfs_realtime_pb2

FEED_BASE = "https://gtfsrt.api.translink.com.au/api/realtime"
REGIONS = ("SEQ", "CNS", "NSI", "MHB", "BOW")
MODES = ("Bus", "Rail", "Tram", "Ferry")
USER_AGENT = "translink-trajectory-collector/2.0"

# Columns are ordered to group related fields; Parquet stores them columnar so
# the order only affects readability, not layout efficiency.
SCHEMA = pa.schema([
    ("vehicle_id", pa.string()),
    ("ts", pa.timestamp("s", tz="UTC")),
    ("vehicle_label", pa.string()),
    ("trip_id", pa.string()),
    ("route_id", pa.string()),
    ("direction_id", pa.int8()),
    ("start_date", pa.string()),
    ("start_time", pa.string()),
    ("lat", pa.float64()),
    ("lon", pa.float64()),
    ("bearing", pa.float32()),
    ("speed", pa.float32()),
    ("odometer", pa.float64()),
    ("stop_id", pa.string()),
    ("current_status", pa.string()),
    ("occupancy_status", pa.string()),
    ("congestion_level", pa.string()),
    ("feed_ts", pa.timestamp("s", tz="UTC")),
    ("fetched_at", pa.timestamp("s", tz="UTC")),
])

HAVERSINE_MACRO = """
CREATE OR REPLACE MACRO haversine(lat1, lon1, lat2, lon2) AS
    2 * 6371008.8 * asin(sqrt(
        pow(sin(radians(lat2 - lat1) / 2), 2)
        + cos(radians(lat1)) * cos(radians(lat2))
          * pow(sin(radians(lon2 - lon1) / 2), 2)
    ))
"""

SUMMARY_SQL = """
WITH deduped AS (
    SELECT * EXCLUDE (rn) FROM (
        SELECT *, row_number() OVER (PARTITION BY vehicle_id, ts) AS rn
        FROM read_parquet('{glob}', hive_partitioning = true)
    ) WHERE rn = 1
),
stepped AS (
    SELECT
        trip_id,
        route_id,
        vehicle_id,
        ts,
        haversine(lag(lat) OVER w, lag(lon) OVER w, lat, lon) AS step_m
    FROM deduped
    WHERE trip_id IS NOT NULL AND lat IS NOT NULL
    WINDOW w AS (PARTITION BY trip_id, vehicle_id ORDER BY ts)
)
SELECT
    trip_id,
    route_id,
    vehicle_id,
    count(*) AS points,
    strftime(min(ts), '%Y-%m-%d %H:%M:%S') AS first_fix,
    strftime(max(ts), '%Y-%m-%d %H:%M:%S') AS last_fix,
    round(epoch(max(ts) - min(ts)) / 60.0, 1) AS minutes,
    round(sum(step_m) / 1000.0, 3) AS km,
    round(max(coalesce(step_m, 0))) AS max_gap_m
FROM stepped
GROUP BY trip_id, route_id, vehicle_id
HAVING count(*) > 1
ORDER BY km DESC
LIMIT {limit}
"""


class Stopped(Exception):
    """Raised when a shutdown signal is received."""


class ParquetSink:
    """Buffers rows and flushes them to partitioned Parquet files."""

    def __init__(self, root, region, batch_size=5000, max_age=300,
                 compression="zstd"):
        self.root = root
        self.region = region
        self.batch_size = batch_size
        self.max_age = max_age
        self.compression = compression
        self.rows = []
        self.last_flush = time.monotonic()
        self.sequence = 0
        self.files_written = 0
        self.rows_written = 0

    def add(self, row):
        self.rows.append(row)

    def should_flush(self):
        if not self.rows:
            return False
        return (len(self.rows) >= self.batch_size
                or time.monotonic() - self.last_flush >= self.max_age)

    def flush(self):
        """Write buffered rows to one Parquet file per partition date."""
        if not self.rows:
            return 0

        by_date = {}
        for row in self.rows:
            stamp = datetime.fromtimestamp(row[1], tz=timezone.utc)
            by_date.setdefault(stamp.strftime("%Y-%m-%d"), []).append(row)

        written = 0
        for partition_date, rows in sorted(by_date.items()):
            written += self._write_partition(partition_date, rows)

        self.rows = []
        self.last_flush = time.monotonic()
        return written

    def _write_partition(self, partition_date, rows):
        directory = os.path.join(self.root,
                                 "dt=%s" % partition_date,
                                 "region=%s" % self.region)
        os.makedirs(directory, exist_ok=True)

        self.sequence += 1
        name = "part-%d-%d-%04d.parquet" % (
            int(time.time()), os.getpid(), self.sequence)
        final_path = os.path.join(directory, name)
        temp_path = os.path.join(directory, "." + name + ".tmp")

        columns = list(zip(*rows))
        table = pa.Table.from_arrays(
            [pa.array(column, type=field.type)
             for column, field in zip(columns, SCHEMA)],
            schema=SCHEMA)

        pq.write_table(table, temp_path, compression=self.compression)
        os.replace(temp_path, final_path)

        self.files_written += 1
        self.rows_written += len(rows)
        return len(rows)


class Deduplicator:
    """Suppresses repeat fixes seen within a rolling window."""

    def __init__(self, window=7200):
        self.window = window
        self.seen = set()
        self.last_prune = time.monotonic()

    def is_new(self, vehicle_id, ts):
        key = (vehicle_id, ts)
        if key in self.seen:
            return False
        self.seen.add(key)
        return True

    def prune(self, now):
        if time.monotonic() - self.last_prune < self.window / 4:
            return
        cutoff = now - self.window
        self.seen = {key for key in self.seen if key[1] >= cutoff}
        self.last_prune = time.monotonic()


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


def parse_feed(payload, fetched_at):
    """Decode a FeedMessage into row tuples matching SCHEMA."""
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
        # fall back to the feed header so the row still has a usable time.
        ts = vehicle.timestamp or feed_ts or fetched_at

        rows.append((
            vehicle_id,
            ts,
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

    return rows


def poll_once(sink, deduper, url, etag, verbose=False):
    """Fetch, parse and buffer one snapshot. Returns the new ETag."""
    fetched_at = int(time.time())
    try:
        payload, new_etag = fetch(url, etag)
    except (urllib.error.URLError, TimeoutError) as error:
        print("fetch failed: %s" % error, file=sys.stderr)
        return etag

    if payload is None:
        if verbose:
            print("feed unchanged (304)")
        return new_etag

    rows = parse_feed(payload, fetched_at)
    fresh = [row for row in rows if deduper.is_new(row[0], row[1])]
    for row in fresh:
        sink.add(row)
    deduper.prune(fetched_at)

    flushed = sink.flush() if sink.should_flush() else 0
    print("%s  entities=%-5d new=%-5d buffered=%-6d flushed=%-6d bytes=%d" % (
        time.strftime("%H:%M:%S", time.localtime(fetched_at)),
        len(rows), len(fresh), len(sink.rows), flushed, len(payload)))
    return new_etag


def run_summary(root, limit):
    """Print per-trip trajectory statistics by querying the Parquet dataset."""
    try:
        import duckdb
    except ImportError:
        print("duckdb is not installed. Either 'pip install duckdb' or query "
              "the dataset directly:\n\n  SELECT * FROM read_parquet('%s/**/*.parquet',\n"
              "                                 hive_partitioning = true);"
              % root, file=sys.stderr)
        return 1

    connection = duckdb.connect()
    connection.execute(HAVERSINE_MACRO)
    glob = os.path.join(root, "**", "*.parquet")
    rows = connection.execute(
        SUMMARY_SQL.format(glob=glob, limit=int(limit))).fetchall()

    if not rows:
        print("No multi-point trips stored yet. Poll for a few minutes first.")
        return 0

    header = ("trip_id", "route", "vehicle", "pts", "first fix", "last fix",
              "mins", "km", "max gap m")
    print("%-26s %-8s %-12s %5s %-20s %-20s %6s %8s %9s" % header)
    for row in rows:
        print("%-26s %-8s %-12s %5s %-20s %-20s %6s %8s %9s" % tuple(
            "" if value is None else str(value)[:26] for value in row))
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Collect Translink GTFS-RT vehicle positions into Parquet.")
    parser.add_argument("--region", default="SEQ", choices=REGIONS,
                        help="Translink region feed (default: SEQ)")
    parser.add_argument("--mode", choices=MODES,
                        help="restrict to one mode; SEQ only")
    parser.add_argument("--root", default="positions",
                        help="dataset root directory (default: positions)")
    parser.add_argument("--interval", type=float, default=20.0,
                        help="seconds between polls (default: 20)")
    parser.add_argument("--batch-size", type=int, default=5000,
                        help="buffered rows before a flush (default: 5000)")
    parser.add_argument("--max-age", type=float, default=300.0,
                        help="seconds before an idle buffer flushes (default: 300)")
    parser.add_argument("--compression", default="zstd",
                        choices=("zstd", "snappy", "gzip", "none"),
                        help="Parquet compression codec (default: zstd)")
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

    if args.summary:
        return run_summary(args.root, args.limit)

    sink = ParquetSink(args.root, args.region,
                       batch_size=args.batch_size,
                       max_age=args.max_age,
                       compression=args.compression)
    deduper = Deduplicator()
    url = feed_url(args.region, args.mode)
    print("polling %s every %.0fs -> %s/" % (url, args.interval, args.root))

    def stop(signum, frame):
        raise Stopped()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    started = time.monotonic()
    etag = None
    try:
        while True:
            etag = poll_once(sink, deduper, url, etag, args.verbose)
            if args.once:
                break
            if args.max_runtime and time.monotonic() - started >= args.max_runtime:
                break
            time.sleep(args.interval)
    except Stopped:
        print("\nstopping")
    finally:
        # Always drain the buffer, otherwise a clean shutdown loses rows.
        sink.flush()
        print("%d rows in %d files under %s/" % (
            sink.rows_written, sink.files_written, args.root))

    return 0


if __name__ == "__main__":
    sys.exit(main())
