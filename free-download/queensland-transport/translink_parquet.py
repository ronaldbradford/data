#!/usr/bin/env python
"""Poll Translink GTFS-Realtime vehicle positions into a partitioned Parquet dataset.

Each row is one timestamped GPS fix for one vehicle on one trip. Repeated
polling accumulates the path a vehicle takes from origin to destination.

With no --region given, the 5 officially documented regions (SEQ, CNS, NSI,
MHB, BOW) are polled each cycle. Pass --all to also poll the undocumented
regions found by probing the API (see README.md), or --region to poll just
one, official or undocumented. --mode narrows to a single vehicle type but
only exists for SEQ, so an unqualified --mode implies --region SEQ.

Output is a Hive-partitioned directory that DuckDB reads directly:

    positions/dt=2026-08-11/region=SEQ/part-1786434892-31337-0003.parquet

Files are written atomically (temp name, then rename), so a reader scanning the
directory never sees a half-written file.

Feed documentation: https://translink.com.au/about-translink/open-data/gtfs-rt
Data licensed CC-BY, State of Queensland. No authentication required.

Requires: pip install gtfs-realtime-bindings pyarrow

Examples:
    ./translink_parquet.py --once                          # snapshot, 5 official regions
    ./translink_parquet.py --all --once                     # snapshot, all 18 known regions
    ./translink_parquet.py --interval 20 --max-runtime 86400
    ./translink_parquet.py --region SEQ --mode Bus --interval 20
    ./translink_parquet.py --region MKY --interval 20        # a single undocumented region
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
# The 5 regions Translink documents at
# https://translink.com.au/about-translink/open-data/gtfs-rt
OFFICIAL_REGIONS = ("SEQ", "CNS", "NSI", "MHB", "BOW")

# Undocumented but working codes, found by probing the realtime API with a
# code guessed from each region name in the static GTFS schedule listing at
# https://www.data.qld.gov.au/dataset/general-transit-feed-specification-gtfs-translink
# See README.md for the full region-name-to-code table.
UNDOCUMENTED_REGIONS = ("BUN", "GLT", "GYM", "INN", "KIL", "MKY", "MAG", "MAL",
                        "RKY", "TWB", "TSV", "WAR", "WHT")

ALL_REGIONS = OFFICIAL_REGIONS + UNDOCUMENTED_REGIONS
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


def poll_once(region, sink, deduper, url, etag, verbose=False):
    """Fetch, parse and buffer one snapshot for one region. Returns the new ETag."""
    fetched_at = int(time.time())
    try:
        payload, new_etag = fetch(url, etag)
    except (urllib.error.URLError, TimeoutError) as error:
        print("%-4s fetch failed: %s" % (region, error), file=sys.stderr)
        return etag

    if payload is None:
        if verbose:
            print("%-4s feed unchanged (304)" % region)
        return new_etag

    rows = parse_feed(payload, fetched_at)
    fresh = [row for row in rows if deduper.is_new(row[0], row[1])]
    for row in fresh:
        sink.add(row)
    deduper.prune(fetched_at)

    flushed = sink.flush() if sink.should_flush() else 0
    print("%s %-4s entities=%-5d new=%-5d buffered=%-6d flushed=%-6d bytes=%d" % (
        time.strftime("%H:%M:%S", time.localtime(fetched_at)),
        region, len(rows), len(fresh), len(sink.rows), flushed, len(payload)))
    return new_etag


SUMMARY_HEADER = ("trip_id", "route", "vehicle", "pts", "first_fix", "last_fix",
                   "mins", "km", "max_gap_m")


def print_summary(rows):
    """Print summary rows as TSV: a header line, then one line per row.

    Tab-separated so the output pipes straight into `column -t -s $'\\t'`
    for aligned columns, or into any other TSV-aware tool.
    """
    print("\t".join(SUMMARY_HEADER))
    for row in rows:
        print("\t".join("" if value is None else str(value) for value in row))


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

    print_summary(rows)
    if not rows:
        print("No multi-point trips stored yet. Poll for a few minutes first.",
              file=sys.stderr)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Collect Translink GTFS-RT vehicle positions into Parquet.")
    parser.add_argument("--region", choices=ALL_REGIONS,
                        help="Translink region feed (default: the 5 official "
                             "regions, or SEQ only when --mode is set)")
    parser.add_argument("--all", action="store_true",
                        help="poll every known region, including undocumented "
                             "ones (see README.md); default is the 5 official "
                             "regions only")
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

    if args.region and args.all:
        parser.error("--region and --all are mutually exclusive")
    if args.mode and args.region and args.region != "SEQ":
        parser.error("mode-specific feeds are only published for SEQ")
    if args.mode and args.all:
        parser.error("mode-specific feeds are only published for SEQ, not --all")
    if args.interval < 5:
        parser.error("interval below 5s is impolite; the feed updates slower than that")

    if args.summary:
        return run_summary(args.root, args.limit)

    if args.region:
        regions = (args.region,)
    elif args.mode:
        # Mode-specific feeds only exist for SEQ, so an unqualified --mode
        # implies --region SEQ rather than looping over every region.
        regions = ("SEQ",)
    elif args.all:
        regions = ALL_REGIONS
    else:
        regions = OFFICIAL_REGIONS

    feeds = []
    for region in regions:
        sink = ParquetSink(args.root, region,
                           batch_size=args.batch_size,
                           max_age=args.max_age,
                           compression=args.compression)
        url = feed_url(region, args.mode)
        print("polling %s every %.0fs -> %s/" % (url, args.interval, args.root))
        feeds.append({"region": region, "sink": sink, "deduper": Deduplicator(),
                     "url": url, "etag": None})

    def stop(signum, frame):
        raise Stopped()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    started = time.monotonic()
    try:
        while True:
            for feed in feeds:
                feed["etag"] = poll_once(feed["region"], feed["sink"],
                                         feed["deduper"], feed["url"],
                                         feed["etag"], args.verbose)
            if args.once:
                break
            if args.max_runtime and time.monotonic() - started >= args.max_runtime:
                break
            time.sleep(args.interval)
    except Stopped:
        print("\nstopping")
    finally:
        # Always drain the buffers, otherwise a clean shutdown loses rows.
        for feed in feeds:
            feed["sink"].flush()
        print("%d rows in %d files under %s/" % (
            sum(feed["sink"].rows_written for feed in feeds),
            sum(feed["sink"].files_written for feed in feeds),
            args.root))

    return 0


if __name__ == "__main__":
    sys.exit(main())
