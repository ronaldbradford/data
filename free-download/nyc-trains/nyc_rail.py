"""Shared feed definitions, static GTFS loading, and GTFS-Realtime parsing
for NYC-area rail: Subway, LIRR, Metro-North and PATH.

Used by both viewer.py (a live map server) and generator.py (a one-shot
GeoJSON emitter) so the two never drift apart on how a feed is fetched or
a train's position is derived — that logic has a couple of real,
easy-to-miss quirks (see parse_feed's docstring) that are worth getting
right exactly once.

Unlike a GPS-tracked fleet, these feeds rarely report a train's lat/lon
directly. Most VehiclePosition entities instead give a stop_id + status
(STOPPED_AT / INCOMING_AT / IN_TRANSIT_TO relative to that stop) — LIRR
and Metro-North occasionally include a raw position too, which is used
in preference when present. Trains reported only via TripUpdate (no
VehiclePosition at all — normal for PATH, which never sends one) are
plotted at the first stop in their upcoming-stops list instead, tagged
SCHEDULED. Station coordinates and route colors come from each agency's
static GTFS dataset, downloaded once and cached to disk alongside this
module; PATH publishes no such dataset alongside its realtime feed, so
its 13 stations/5 routes are hardcoded below instead.
"""

import csv
import io
import json
import os
import time
import urllib.error
import urllib.request
import zipfile

from google.transit import gtfs_realtime_pb2

MTA_FEED_BASE = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds"
# Each feed_id is a line "group" as published, mapped to its upstream URL
# and which static dataset (agency key, below) supplies its station
# coordinates and route colors. MTA subway shuttles ride along with their
# parent division's feed (GS/FS with 1234567S, H with ACE).
FEEDS = {
    "1234567S": {"url": MTA_FEED_BASE + "/nyct%2Fgtfs",      "agency": "subway"},  # 1 2 3 4 5 6 6X 7 7X GS
    "ACE":      {"url": MTA_FEED_BASE + "/nyct%2Fgtfs-ace",  "agency": "subway"},  # A C E H (Rockaway Park Shuttle)
    "BDFM":     {"url": MTA_FEED_BASE + "/nyct%2Fgtfs-bdfm", "agency": "subway"},  # B D F FX M
    "G":        {"url": MTA_FEED_BASE + "/nyct%2Fgtfs-g",    "agency": "subway"},
    "JZ":       {"url": MTA_FEED_BASE + "/nyct%2Fgtfs-jz",   "agency": "subway"},
    "NQRW":     {"url": MTA_FEED_BASE + "/nyct%2Fgtfs-nqrw", "agency": "subway"},
    "L":        {"url": MTA_FEED_BASE + "/nyct%2Fgtfs-l",    "agency": "subway"},
    "SI":       {"url": MTA_FEED_BASE + "/nyct%2Fgtfs-si",   "agency": "subway"},  # Staten Island Railway
    "LIRR":     {"url": MTA_FEED_BASE + "/lirr%2Fgtfs-lirr", "agency": "lirr"},
    "MNR":      {"url": MTA_FEED_BASE + "/mnr%2Fgtfs-mnr",   "agency": "mnr"},
    "PATH":     {"url": "https://path.transitdata.nyc/gtfsrt", "agency": "path"},
}
# Display grouping used by viewer.py's dropdown, in display order.
FEED_GROUPS = [
    ("Subway", ["1234567S", "ACE", "BDFM", "G", "JZ", "NQRW", "L", "SI"]),
    ("Commuter Rail", ["LIRR", "MNR"]),
    ("PATH", ["PATH"]),
]
DEFAULT_FEED = "1234567S"
USER_AGENT = "nyc-rail-viewer/1.0"

# Static GTFS (stop locations + route colors), not realtime — refreshed
# rarely, so it's cached to disk rather than fetched on every poll. One
# dataset per agency; stop ids are not unique *across* agencies (e.g.
# LIRR stop "1" and Metro-North stop "1" are different stations), so
# these are kept as separate namespaces, never merged.
STATIC_GTFS_URLS = {
    "subway": "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip",
    "lirr": "https://rrgtfsfeeds.s3.amazonaws.com/gtfslirr.zip",
    "mnr": "https://rrgtfsfeeds.s3.amazonaws.com/gtfsmnr.zip",
}
STATIC_CACHE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".nyc_rail_static_cache.json")
STATIC_CACHE_MAX_AGE = 30 * 24 * 3600  # station locations/colors rarely change

# PATH has no static GTFS published alongside its realtime feed, so its
# small, stable set of stations/routes is hardcoded here instead. Stop
# ids and station->id mapping from the realtime feed's own source
# (github.com/jamespfennell/path-train-gtfs-realtime); coordinates are
# each station's well-known public location. Route colors are
# approximations of PATH's line branding, not an official PANYNJ source.
PATH_STOPS = {
    "26722": {"name": "14th Street", "lat": 40.7376, "lon": -74.0002},
    "26723": {"name": "23rd Street", "lat": 40.7430, "lon": -73.9971},
    "26724": {"name": "33rd Street", "lat": 40.7499, "lon": -73.9885},
    "26725": {"name": "9th Street", "lat": 40.7339, "lon": -74.0006},
    "26726": {"name": "Christopher Street", "lat": 40.7328, "lon": -74.0068},
    "26727": {"name": "Exchange Place", "lat": 40.7164, "lon": -74.0329},
    "26728": {"name": "Grove Street", "lat": 40.7196, "lon": -74.0431},
    "26729": {"name": "Harrison", "lat": 40.7392, "lon": -74.1559},
    "26730": {"name": "Hoboken", "lat": 40.7359, "lon": -74.0292},
    "26731": {"name": "Journal Square", "lat": 40.7328, "lon": -74.0629},
    "26732": {"name": "Newport", "lat": 40.7272, "lon": -74.0338},
    "26733": {"name": "Newark", "lat": 40.7342, "lon": -74.1645},
    "26734": {"name": "World Trade Center", "lat": 40.7128, "lon": -74.0099},
}
PATH_ROUTES = {
    "859":  {"color": "FCB61A", "text_color": "000000", "name": "H3", "long_name": "Hoboken – 33rd Street"},
    "860":  {"color": "4D92FB", "text_color": "000000", "name": "HW", "long_name": "Hoboken – World Trade Center"},
    "861":  {"color": "FFC61E", "text_color": "000000", "name": "J3", "long_name": "Journal Square – 33rd Street"},
    "862":  {"color": "EE2E24", "text_color": "FFFFFF", "name": "NW", "long_name": "Newark – World Trade Center"},
    "1024": {"color": "6E6E6E", "text_color": "FFFFFF", "name": "J3H", "long_name": "Journal Square – 33rd Street (via Hoboken)"},
}


def fetch(url, etag=None, timeout=15):
    """Fetch a payload. Returns (payload, etag); payload is None on 304."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    if etag:
        request.add_header("If-None-Match", etag)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read(), response.headers.get("ETag")
    except urllib.error.HTTPError as error:
        if error.code == 304:
            return None, etag
        raise


def download_gtfs_stops_and_routes(url):
    """Download one agency's static GTFS zip and pull out just what the
    map needs: station id -> (name, lat, lon), and route id -> (color,
    short/long name)."""
    payload, _ = fetch(url, timeout=60)
    archive = zipfile.ZipFile(io.BytesIO(payload))

    stops = {}
    with archive.open("stops.txt") as raw:
        for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig")):
            try:
                lat, lon = float(row["stop_lat"]), float(row["stop_lon"])
            except (KeyError, ValueError):
                continue
            stops[row["stop_id"]] = {"name": row["stop_name"], "lat": lat, "lon": lon}

    routes = {}
    with archive.open("routes.txt") as raw:
        for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig")):
            short = row.get("route_short_name") or None
            long_ = row.get("route_long_name") or None
            routes[row["route_id"]] = {
                "color": row.get("route_color") or "6E6E6E",
                "text_color": row.get("route_text_color") or "FFFFFF",
                "name": short or row["route_id"],
                "long_name": long_ or short or row["route_id"],
            }

    return {"stops": stops, "routes": routes}


def load_static_data(force_refresh=False):
    """Cached on disk so every run after the first skips re-downloading
    multi-megabyte zips just to plot the same stations. Covers every
    agency in one cache file."""
    if not force_refresh and os.path.exists(STATIC_CACHE_PATH):
        age = time.time() - os.path.getmtime(STATIC_CACHE_PATH)
        if age < STATIC_CACHE_MAX_AGE:
            with open(STATIC_CACHE_PATH) as f:
                return json.load(f)

    data = {agency: download_gtfs_stops_and_routes(url)
            for agency, url in STATIC_GTFS_URLS.items()}
    data["path"] = {"stops": PATH_STOPS, "routes": PATH_ROUTES}
    data["fetched_at"] = time.time()
    with open(STATIC_CACHE_PATH, "w") as f:
        json.dump(data, f)
    return data


def enum_name(descriptor, value):
    try:
        return descriptor.Name(value)
    except ValueError:
        return str(value)


def parse_feed(payload, stops):
    """Decode a FeedMessage into JSON-ready train dicts, one per trip.

    A pre-pass collects (route_id, start_date) from every TripUpdate
    first, keyed by its trip id — LIRR's VehiclePosition.trip never sets
    route_id at all (only its separate TripUpdate entity does), so this
    is the only reliable source for it; a vehicle-only trip with no
    matching TripUpdate anywhere falls back to its own trip fields.

    Pass 1 looks at VehiclePosition entities for a reported stop_id
    and/or raw lat/lon. Metro-North bundles a VehiclePosition and a
    TripUpdate in the *same* FeedEntity, but confusingly gives them
    different trip ids — the vehicle side's trip.trip_id is actually the
    physical train/engine number, not the trip id — so when both are
    present on one entity, the TripUpdate's trip id is used as the join
    key throughout.

    Pass 2 covers every trip pass 1 didn't place: represented only by a
    TripUpdate (PATH always; others when a train hasn't reported a
    position yet), plotted at the first upcoming stop and tagged
    SCHEDULED.
    """
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(payload)

    trip_meta = {}  # trip_id -> (route_id, start_date)
    for entity in feed.entity:
        if entity.HasField("trip_update"):
            trip = entity.trip_update.trip
            if trip.trip_id:
                trip_meta[trip.trip_id] = (trip.route_id, trip.start_date)

    by_trip = {}  # trip_id -> {stop_id, stop_name, lat, lon, status, ts}

    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue
        vehicle = entity.vehicle
        has_stop = vehicle.HasField("stop_id")
        has_pos = vehicle.HasField("position")
        if not has_stop and not has_pos:
            continue

        if entity.HasField("trip_update") and entity.trip_update.trip.trip_id:
            trip_id = entity.trip_update.trip.trip_id
        else:
            trip_id = vehicle.trip.trip_id
        if not trip_id:
            continue
        trip_meta.setdefault(trip_id, (vehicle.trip.route_id, vehicle.trip.start_date))

        record = {
            "stop_id": vehicle.stop_id if has_stop else None,
            "status": enum_name(
                gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus, vehicle.current_status),
            "ts": vehicle.timestamp or None,
        }
        if has_pos:
            record["lat"] = vehicle.position.latitude
            record["lon"] = vehicle.position.longitude
            record["stop_name"] = stops.get(vehicle.stop_id, {}).get("name") if has_stop else None
        else:
            stop = stops.get(vehicle.stop_id)
            if not stop:
                continue  # stop_id not in the static dataset (shouldn't normally happen)
            record["lat"], record["lon"], record["stop_name"] = stop["lat"], stop["lon"], stop["name"]

        by_trip[trip_id] = record

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        trip_update = entity.trip_update
        trip = trip_update.trip
        if not trip.trip_id:
            continue
        if trip.trip_id in by_trip:
            continue  # already positioned in pass 1
        if not trip_update.stop_time_update:
            continue
        first = trip_update.stop_time_update[0]
        stop = stops.get(first.stop_id)
        if not stop:
            continue
        eta = None
        if first.HasField("arrival"):
            eta = first.arrival.time
        elif first.HasField("departure"):
            eta = first.departure.time
        by_trip[trip.trip_id] = {
            "stop_id": first.stop_id,
            "stop_name": stop["name"],
            "lat": stop["lat"],
            "lon": stop["lon"],
            "status": "SCHEDULED",
            "ts": eta,
        }

    trains = []
    for trip_id, info in by_trip.items():
        route_id, start_date = trip_meta[trip_id]
        direction = None
        if info.get("stop_id"):
            # Subway/PATH-style stop ids end in N/S for platform direction;
            # LIRR/Metro-North stop ids don't, so this is simply None there.
            direction = {"N": "Uptown/Northbound", "S": "Downtown/Southbound"}.get(
                info["stop_id"][-1:])
        trains.append({
            "trip_id": trip_id,
            "route_id": route_id or None,
            "start_date": start_date or None,
            "stop_id": info.get("stop_id"),
            "stop_name": info.get("stop_name"),
            "direction": direction,
            "lat": info["lat"],
            "lon": info["lon"],
            "status": info["status"],
            "ts": info["ts"],
        })
    return trains


def fetch_trains(feed_id, static_data, etag=None):
    """Convenience wrapper: fetch + parse one feed_id's current trains
    using the matching agency's stops from static_data (as returned by
    load_static_data()). Returns (trains, new_etag); trains is None on a
    304 Not Modified (caller should keep using its last-known trains)."""
    payload, new_etag = fetch(FEEDS[feed_id]["url"], etag=etag)
    if payload is None:
        return None, new_etag
    stops = static_data[FEEDS[feed_id]["agency"]]["stops"]
    return parse_feed(payload, stops), new_etag
