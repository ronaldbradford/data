#!/usr/bin/env python
"""Emit current NYC-area rail positions (Subway, LIRR, Metro-North, PATH)
as GeoJSON FeatureCollections on stdout — one per line, never combined,
so each output line is a self-contained snapshot of a single feed.

A snapshot generator, not a collector — nothing is stored, and each
snapshot fetches fresh data. Meant to be redirected to a file and used as
a data source for another map tool (Leaflet, Mapbox GL, kepler.gl,
tippecanoe, QGIS, geojson.io, ...).

By default it emits one FeatureCollection per line and exits — 11 lines
of NDJSON for the default full set, one line of NDJSON for a single
--line. Pass -n/--count to repeat the whole set of lines several times,
-i/--interval seconds apart (see -h for the exact defaulting rules).
Run it once under a scheduler (cron, a systemd timer) for a
periodically-refreshed file, or run it with -n/-i to have it do its own
scheduling for a long-lived stream.

Shares its feed definitions, static station/route data, and
GTFS-Realtime parsing with viewer/viewer.py — see ../nyc_rail.py for how
positions are derived (most of these feeds report a stop_id + status
rather than raw GPS; that module's docstring has the details, including
a Metro-North trip-id quirk it works around).

Only stdout carries GeoJSON — everything else (progress, per-line fetch
errors) goes through the `logging` module to stderr by default, so
`./generator.py > trains.geojson` always gets valid JSON/NDJSON even if
one line's upstream feed is temporarily down. Use --log-file to send that
output to a file instead, e.g. when running unattended with -n/-i and
stdout is itself being redirected to a file.

Requires: pip install gtfs-realtime-bindings

Usage:
    ./generator.py                        # one FeatureCollection per line, to stdout
    ./generator.py > trains.ndjson
    ./generator.py --line LIRR            # a single line -> a single FeatureCollection
    ./generator.py -n 5                   # repeat the whole set 5 times, 20s apart (default interval when -n given alone)
    ./generator.py -n 60 -i 10            # repeat 60 times, 10s apart
    ./generator.py --line 1234567S ACE
    ./generator.py --line LIRR --route 1 3
    ./generator.py --no-scheduled         # drop trains not yet positioned (TripUpdate-only)
    ./generator.py --pretty
    ./generator.py --refresh-static       # force re-download of station/route data first
    ./generator.py -n 60 -i 10 --log-file generator.log > trains.ndjson
    ./generator.py --sql | mysql your_db  # INSERTs into nyc_trains (see 02-tables.sql)
"""

import argparse
import datetime
import json
import logging
import os
import sys
import time

# nyc_rail.py is shared with viewer/viewer.py, so it lives one level up
# rather than under either — not importable by its plain module name
# until that directory is on sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import nyc_rail  # noqa: E402

logger = logging.getLogger("generator")


def build_feature(train, feed_id, routes):
    info = routes.get(train["route_id"]) or {}
    ts = train.get("ts")
    updated = None
    if ts:
        updated = datetime.datetime.fromtimestamp(
            ts, tz=datetime.timezone.utc).isoformat()
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [train["lon"], train["lat"]]},
        "properties": {
            "line": feed_id,
            "trip_id": train["trip_id"],
            "route_id": train["route_id"],
            "route_name": info.get("name"),
            "route_long_name": info.get("long_name"),
            "route_color": ("#" + info["color"]) if info.get("color") else None,
            "start_date": train["start_date"],
            "stop_id": train["stop_id"],
            "stop_name": train["stop_name"],
            "direction": train["direction"],
            "status": train["status"],
            "ts": ts,
            "updated": updated,
        },
    }


def sql_escape(value):
    # Backslash must be escaped first: MySQL's default SQL_MODE treats it
    # as a string-literal escape character (unless NO_BACKSLASH_ESCAPES is
    # set), so a literal backslash already in the value — e.g. the \uXXXX
    # json.dumps emits for every non-ASCII character, since it defaults to
    # ensure_ascii=True — would otherwise be silently consumed by the SQL
    # parser and corrupt the embedded JSON. Doubling the single quote
    # after that is standard SQL and valid under NO_BACKSLASH_ESCAPES too.
    return value.replace("\\", "\\\\").replace("'", "''")


def build_insert_sql(collection):
    """Render one line's FeatureCollection as an INSERT into the
    nyc_trains table (see 02-tables.sql) — generated_at/line/train_count
    are pulled out as their own columns, and the collection itself (the
    same object that would otherwise be written as a line of JSON) is
    stored verbatim in the position column."""
    generated_at = datetime.datetime.fromisoformat(
        collection["generated_at"]).strftime("%Y-%m-%d %H:%M:%S.%f")
    return ("INSERT INTO nyc_trains (generated_at, line, train_count, position) "
             "VALUES ('%s', '%s', %d, '%s');") % (
        generated_at, sql_escape(collection["line"]), len(collection["features"]),
        sql_escape(json.dumps(collection, separators=(",", ":"))))


def build_line_snapshot(feed_id, route_filter, no_scheduled, static_data):
    """Fetch and parse one line's feed and return its FeatureCollection.
    Returns None (after logging why) if the fetch/parse raised."""
    agency = nyc_rail.FEEDS[feed_id]["agency"]
    stops = static_data[agency]["stops"]
    routes = static_data[agency]["routes"]
    try:
        payload, _ = nyc_rail.fetch(nyc_rail.FEEDS[feed_id]["url"])
        trains = nyc_rail.parse_feed(payload, stops)
    except Exception as error:
        logger.warning("%s: %s: %s", feed_id, type(error).__name__, error)
        return None

    features = []
    for train in trains:
        if no_scheduled and train["status"] == "SCHEDULED":
            continue
        if route_filter and train["route_id"] not in route_filter:
            continue
        features.append(build_feature(train, feed_id, routes))

    return {
        "type": "FeatureCollection",
        # Not part of the GeoJSON spec, but harmless extra metadata that
        # every mainstream consumer (Leaflet, Mapbox GL, QGIS...) ignores
        # rather than rejects — useful for a consumer to judge freshness.
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "line": feed_id,
        "features": features,
    }


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Emit current NYC-area rail positions (Subway, LIRR, "
                     "Metro-North, PATH) as a GeoJSON FeatureCollection on "
                     "stdout.")
    parser.add_argument("--line", nargs="+", choices=sorted(nyc_rail.FEEDS), metavar="LINE",
                        help="restrict to these line(s) (default: every line — "
                             "%s)" % ", ".join(sorted(nyc_rail.FEEDS)))
    parser.add_argument("--route", nargs="+", metavar="ROUTE_ID",
                        help="restrict to these route id(s) exactly, e.g. "
                             "--route 6 A (applies across whichever --line(s) "
                             "are selected)")
    parser.add_argument("--no-scheduled", action="store_true",
                        help="drop trains with no reported position, only a "
                             "predicted next stop (status=SCHEDULED) — this is "
                             "every PATH train, and some Subway/LIRR/"
                             "Metro-North trains that haven't started "
                             "reporting yet")
    parser.add_argument("-n", "--count", type=int, default=None, metavar="N",
                        help="number of times to repeat the whole set of "
                             "line(s) (default: 1). Each line's "
                             "FeatureCollection is always its own JSON "
                             "object on its own line — stdout is "
                             "newline-delimited GeoJSON (NDJSON) whenever "
                             "more than one is emitted, whether from "
                             "multiple --line or from N > 1")
    parser.add_argument("-i", "--interval", type=float, default=None, metavar="SECONDS",
                        help="seconds to sleep between repeats (only "
                             "relevant when -n/--count > 1). Default: 20 if "
                             "-n/--count is given without this; 0 (no "
                             "repeat) otherwise. Below 5s is rejected as "
                             "impolite to the upstream feeds")
    parser.add_argument("--pretty", action="store_true",
                        help="indent each line's JSON for readability "
                             "(default: compact, one line per line/feed). "
                             "This makes stdout no longer one-object-per-"
                             "output-line NDJSON — fine to inspect by eye, "
                             "but not fine to stream-parse")
    parser.add_argument("--sql", action="store_true",
                        help="emit a MySQL INSERT statement per line instead "
                             "of raw GeoJSON, for the nyc_trains table (see "
                             "02-tables.sql) — generated_at/line/train_count "
                             "as columns, the FeatureCollection itself in "
                             "the position column. Mutually exclusive with "
                             "--pretty")
    parser.add_argument("--refresh-static", action="store_true",
                        help="force re-download of station locations/route "
                             "colors instead of using the on-disk cache")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="logging verbosity (default: INFO)")
    parser.add_argument("--log-file", metavar="PATH",
                        help="write log messages here instead of stderr — "
                             "handy with -n/-i, where stdout is usually "
                             "redirected to a file of its own")
    args = parser.parse_args()

    log_kwargs = {"filename": args.log_file} if args.log_file else {"stream": sys.stderr}
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(message)s",
        **log_kwargs)

    # Defaulting rules: with neither -n nor -i, emit exactly one snapshot
    # immediately (unchanged single-shot behavior). -n alone repeats every
    # 20s. -i alone is a no-op — count still defaults to 1 — since there's
    # nothing to space out with only one snapshot; flagged rather than
    # silently ignored, in case that's not what was intended.
    count = args.count if args.count is not None else 1
    if count < 1:
        parser.error("-n/--count must be at least 1")
    if args.interval is not None:
        interval = args.interval
    elif args.count is not None:
        interval = 20.0
    else:
        interval = 0.0
    if count > 1 and interval < 5:
        parser.error("interval below 5s is impolite; the feeds don't update that fast")
    if args.interval is not None and args.count is None:
        logger.warning("-i/--interval has no effect without -n/--count > 1 "
                        "(only one snapshot will be emitted)")
    if args.sql and args.pretty:
        parser.error("--sql and --pretty are mutually exclusive "
                      "(SQL statements are always one line)")

    lines = args.line or sorted(nyc_rail.FEEDS)
    route_filter = set(args.route) if args.route else None

    logger.info("loading station locations and route colors...")
    try:
        static_data = nyc_rail.load_static_data(force_refresh=args.refresh_static)
    except Exception as error:
        logger.error("failed to load static GTFS data: %s: %s",
                      type(error).__name__, error)
        return 1

    any_total_failure = False
    for i in range(count):
        prefix = "[%d/%d] " % (i + 1, count) if count > 1 else ""
        total_features = 0
        failed = []
        for feed_id in lines:
            collection = build_line_snapshot(feed_id, route_filter, args.no_scheduled, static_data)
            if collection is None:
                failed.append(feed_id)
                continue
            if args.sql:
                sys.stdout.write(build_insert_sql(collection))
            else:
                json.dump(collection, sys.stdout,
                          indent=2 if args.pretty else None,
                          separators=None if args.pretty else (",", ":"))
            sys.stdout.write("\n")
            sys.stdout.flush()
            total_features += len(collection["features"])
            logger.info("%s%s: %d train(s)", prefix, feed_id, len(collection["features"]))

        if len(lines) > 1:
            logger.info("%s%d train(s) total from %d/%d line(s)%s", prefix,
                        total_features, len(lines) - len(failed), len(lines),
                        " (failed: %s)" % ", ".join(failed) if failed else "")
        if failed and len(failed) == len(lines):
            any_total_failure = True

        if i < count - 1:
            logger.info("waiting %gs before next snapshot...", interval)
            time.sleep(interval)

    return 1 if any_total_failure else 0


if __name__ == "__main__":
    sys.exit(main())
