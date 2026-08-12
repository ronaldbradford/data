#!/usr/bin/env python
"""Collect Transport for NSW GTFS-Realtime vehicle positions into Parquet.

Polls several mode-specific feeds concurrently and writes a Hive-partitioned
dataset that DuckDB reads directly:

    positions/dt=2026-08-11/feed=buses/part-1786435961-529-0001.parquet

The API key is read from a .env file (or the environment). Create .env as:

    TFNSW_API_KEY=your_key_here

and keep it out of version control. Register for a free key at
https://opendata.transport.nsw.gov.au/

Requires: pip install gtfs-realtime-bindings pyarrow

Examples:
    ./tfnsw_collect.py --check                  # verify key and endpoints
    ./tfnsw_collect.py --feeds buses --once
    ./tfnsw_collect.py --interval 15 --max-runtime 86400
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
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pyarrow as pa
import pyarrow.parquet as pq
from google.transit import gtfs_realtime_pb2

API_BASE = "https://api.transport.nsw.gov.au"
USER_AGENT = "tfnsw-trajectory-collector/1.0"
ENV_VAR = "TFNSW_API_KEY"

# TfNSW splits vehicle positions across mode endpoints. v2 supersedes v1 for
# Sydney Trains, Metro and Inner West Light Rail. Run --check to confirm which
# of these your key can reach; the catalogue does change.
FEEDS = {
    "buses": "/v1/gtfs/vehiclepos/buses",
    "ferries": "/v1/gtfs/vehiclepos/ferries/sydneyferries",
    "nswtrains": "/v1/gtfs/vehiclepos/nswtrains",
    "lightrail_cbd": "/v1/gtfs/vehiclepos/lightrail/cbdandsoutheast",
    "lightrail_newcastle": "/v1/gtfs/vehiclepos/lightrail/newcastle",
    "lightrail_innerwest": "/v2/gtfs/vehiclepos/lightrail/innerwest",
    "sydneytrains": "/v2/gtfs/vehiclepos/sydneytrains",
    "metro": "/v2/gtfs/vehiclepos/metro",
}

DEFAULT_FEEDS = ("buses", "ferries", "sydneytrains", "metro")

# Feeds whose vehicles publish upcoming trips alongside the current one.
TRAIL_FEEDS = ("ferries",)

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


class Stopped(Exception):
    """Raised when a shutdown signal is received."""


def load_dotenv(path=".env", override=False):
    """Read KEY=VALUE pairs from a .env file into os.environ.

    Deliberately minimal: handles comments, blank lines, an optional 'export'
    prefix and single or double quoted values. Existing environment variables
    win unless override is set, so a shell export beats the file.
    """
    if not os.path.exists(path):
        return {}

    loaded = {}
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if not key:
                continue
            loaded[key] = value
            if override or key not in os.environ:
                os.environ[key] = value
    return loaded


def resolve_api_key(env_path):
    """Find the API key, preferring the environment over the .env file."""
    load_dotenv(env_path)
    key = os.environ.get(ENV_VAR, "").strip()
    if not key:
        raise SystemExit(
            "No API key found. Set %s in the environment or in %s:\n\n"
            "    %s=your_key_here\n\n"
            "Register for a free key at https://opendata.transport.nsw.gov.au/"
            % (ENV_VAR, env_path, ENV_VAR))
    return key


def fetch(url, api_key, etag=None, timeout=30):
    """Fetch the protobuf payload. Returns (payload, etag); payload is None on 304."""
    request = urllib.request.Request(url, headers={
        "Authorization": "apikey %s" % api_key,
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
        if error.code in (401, 403):
            raise SystemExit(
                "HTTP %d from %s. The API key was rejected. Check %s is correct "
                "and that your account has access to this feed."
                % (error.code, url, ENV_VAR))
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

        ts = vehicle.timestamp or feed_ts or fetched_at

        # Vehicles without a current GPS fix report 0.0/0.0 ("null island").
        # Keep the row for its status fields but drop the bogus coordinates,
        # so distance queries filtering on lat IS NOT NULL stay correct.
        latitude = position.latitude if position.HasField("latitude") else None
        longitude = position.longitude if position.HasField("longitude") else None
        if latitude == 0.0 and longitude == 0.0:
            latitude = longitude = None

        rows.append((
            vehicle_id,
            ts,
            descriptor.label or None,
            trip.trip_id or None,
            trip.route_id or None,
            trip.direction_id if trip.HasField("direction_id") else None,
            trip.start_date or None,
            trip.start_time or None,
            latitude,
            longitude,
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


def collapse_future_trips(rows):
    """Keep one row per vehicle_id, the earliest scheduled trip.

    TfNSW's ferry feed publishes a vehicle's current position alongside its
    upcoming trips, which renders as a trail of phantom ferries. Their guidance
    is to treat vehicle.id as the unique identifier; the earliest start_date +
    start_time is the trip actually running.
    """
    best = {}
    for row in rows:
        vehicle_id = row[0]
        sort_key = ((row[6] or ""), (row[7] or ""))
        existing = best.get(vehicle_id)
        if existing is None or sort_key < existing[0]:
            best[vehicle_id] = (sort_key, row)
    return [entry[1] for entry in best.values()]


class ParquetSink:
    """Buffers rows per feed and flushes them to partitioned Parquet files."""

    def __init__(self, root, feed, batch_size=5000, max_age=300,
                 compression="zstd"):
        self.root = root
        self.feed = feed
        self.batch_size = batch_size
        self.max_age = max_age
        self.compression = compression
        self.rows = []
        self.last_flush = time.monotonic()
        self.sequence = 0
        self.files_written = 0
        self.rows_written = 0

    def add_all(self, rows):
        self.rows.extend(rows)

    def should_flush(self):
        if not self.rows:
            return False
        return (len(self.rows) >= self.batch_size
                or time.monotonic() - self.last_flush >= self.max_age)

    def flush(self):
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
                                 "feed=%s" % self.feed)
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


class FeedCollector:
    """Owns the sink, dedupe state and ETag for one mode endpoint."""

    def __init__(self, name, api_key, root, **sink_options):
        self.name = name
        self.api_key = api_key
        self.url = API_BASE + FEEDS[name]
        self.sink = ParquetSink(root, name, **sink_options)
        self.deduper = Deduplicator()
        self.etag = None

    def poll(self):
        """Fetch and buffer one snapshot. Returns a short status string."""
        fetched_at = int(time.time())
        try:
            payload, self.etag = fetch(self.url, self.api_key, self.etag)
        except (urllib.error.URLError, TimeoutError) as error:
            return "%-13s FAILED %s" % (self.name, error)

        if payload is None:
            return "%-13s unchanged" % self.name

        rows = parse_feed(payload, fetched_at)
        raw_count = len(rows)
        if self.name in TRAIL_FEEDS:
            rows = collapse_future_trips(rows)

        fresh = [row for row in rows if self.deduper.is_new(row[0], row[1])]
        self.sink.add_all(fresh)
        self.deduper.prune(fetched_at)
        flushed = self.sink.flush() if self.sink.should_flush() else 0

        return "%-13s entities=%-5d kept=%-5d new=%-5d flushed=%-6d %dB" % (
            self.name, raw_count, len(rows), len(fresh), flushed, len(payload))


def check_feeds(api_key, names):
    """Probe each endpoint and report what the key can actually reach."""
    print("%-13s %-8s %-9s %s" % ("feed", "status", "entities", "url"))
    ok = 0
    for name in names:
        url = API_BASE + FEEDS[name]
        try:
            payload, _ = fetch(url, api_key)
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(payload)
            print("%-13s %-8s %-9d %s" % (name, "ok", len(feed.entity), url))
            ok += 1
        except urllib.error.HTTPError as error:
            print("%-13s HTTP %-3d %-9s %s" % (name, error.code, "-", url))
        except Exception as error:
            print("%-13s %-8s %-9s %s (%s)" % (name, "error", "-", url, error))
    print("\n%d of %d feeds reachable" % (ok, len(names)))
    return 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(
        description="Collect TfNSW GTFS-RT vehicle positions into Parquet.")
    parser.add_argument("--feeds", nargs="+", choices=sorted(FEEDS),
                        default=list(DEFAULT_FEEDS),
                        help="which mode feeds to poll (default: %s)"
                             % " ".join(DEFAULT_FEEDS))
    parser.add_argument("--env-file", default=".env",
                        help="path to the .env file (default: .env)")
    parser.add_argument("--root", default="positions",
                        help="dataset root directory (default: positions)")
    parser.add_argument("--interval", type=float, default=15.0,
                        help="seconds between polls (default: 15, matching "
                             "TfNSW's documented refresh rate)")
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--max-age", type=float, default=300.0)
    parser.add_argument("--compression", default="zstd",
                        choices=("zstd", "snappy", "gzip", "none"))
    parser.add_argument("--max-runtime", type=float,
                        help="stop after this many seconds")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--check", action="store_true",
                        help="probe every configured endpoint and exit")
    args = parser.parse_args()

    api_key = resolve_api_key(args.env_file)

    if args.check:
        return check_feeds(api_key, sorted(FEEDS))

    collectors = [
        FeedCollector(name, api_key, args.root,
                      batch_size=args.batch_size,
                      max_age=args.max_age,
                      compression=args.compression)
        for name in args.feeds
    ]
    print("polling %s every %.0fs -> %s/"
          % (", ".join(args.feeds), args.interval, args.root))

    def stop(signum, frame):
        raise Stopped()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    started = time.monotonic()
    pool = ThreadPoolExecutor(max_workers=len(collectors))
    try:
        while True:
            stamp = time.strftime("%H:%M:%S")
            for line in pool.map(lambda c: c.poll(), collectors):
                print("%s  %s" % (stamp, line))
            if args.once:
                break
            if args.max_runtime and time.monotonic() - started >= args.max_runtime:
                break
            time.sleep(args.interval)
    except Stopped:
        print("\nstopping")
    finally:
        pool.shutdown(wait=True)
        total_rows = 0
        total_files = 0
        for collector in collectors:
            collector.sink.flush()
            total_rows += collector.sink.rows_written
            total_files += collector.sink.files_written
        print("%d rows in %d files under %s/" % (total_rows, total_files, args.root))

    return 0


if __name__ == "__main__":
    sys.exit(main())
