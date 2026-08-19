#!/usr/bin/env python
"""Local real-time map viewer for Translink vehicle positions.

Serves a single-page Leaflet map in the browser that polls this local
server, which in turn polls the *live* Translink GTFS-Realtime feed for
whichever region/mode is selected in the page's dropdowns. Nothing is
stored — this is a live viewer, not the collector (see
translink_parquet.py for that, and current_positions.py to plot the last
collected fix per vehicle from already-stored data).

Requires: pip install gtfs-realtime-bindings

Usage:
    ./viewer.py                          # http://127.0.0.1:8765, refresh every 20s
    ./viewer.py --port 9000 --interval 10
    ./viewer.py --host 0.0.0.0           # expose beyond localhost (e.g. LAN demo)
"""

import argparse
import gzip
import io
import json
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from google.transit import gtfs_realtime_pb2

FEED_BASE = "https://gtfsrt.api.translink.com.au/api/realtime"
OFFICIAL_REGIONS = ("SEQ", "CNS", "NSI", "MHB", "BOW")
UNDOCUMENTED_REGIONS = ("BUN", "GLT", "GYM", "INN", "KIL", "MKY", "MAG", "MAL",
                        "RKY", "TWB", "TSV", "WAR", "WHT")
ALL_REGIONS = OFFICIAL_REGIONS + UNDOCUMENTED_REGIONS
MODES = ("Bus", "Rail", "Tram", "Ferry")
USER_AGENT = "translink-viewer/1.0"


def feed_url(region, mode=None):
    url = "%s/%s/VehiclePositions" % (FEED_BASE, region)
    if mode:
        url = "%s/%s" % (url, mode)
    return url


def fetch(url, etag=None, timeout=15):
    """Fetch the protobuf payload. Returns (payload, etag); payload is None on 304."""
    request = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip",
    })
    if etag:
        request.add_header("If-None-Match", etag)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read()
        if response.headers.get("Content-Encoding") == "gzip":
            payload = gzip.GzipFile(fileobj=io.BytesIO(payload)).read()
        return payload, response.headers.get("ETag")


def enum_name(descriptor, value):
    try:
        return descriptor.Name(value)
    except ValueError:
        return str(value)


def parse_feed(payload):
    """Decode a FeedMessage into JSON-ready vehicle dicts."""
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(payload)
    vehicles = []

    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue
        vehicle = entity.vehicle
        descriptor = vehicle.vehicle
        trip = vehicle.trip
        position = vehicle.position

        if not position.HasField("latitude") or not position.HasField("longitude"):
            continue

        vehicles.append({
            "vehicle_id": descriptor.id or entity.id or None,
            "label": descriptor.label or None,
            "trip_id": trip.trip_id or None,
            "route_id": trip.route_id or None,
            "lat": position.latitude,
            "lon": position.longitude,
            "bearing": position.bearing if position.HasField("bearing") else None,
            "speed": position.speed if position.HasField("speed") else None,
            "current_status": enum_name(
                gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus, vehicle.current_status),
            "occupancy_status": enum_name(
                gtfs_realtime_pb2.VehiclePosition.OccupancyStatus, vehicle.occupancy_status),
            "ts": vehicle.timestamp or None,
        })

    return vehicles


class FeedCache:
    """Per (region, mode) cache so concurrent/rapid browser polls never hit
    the upstream feed more often than --interval, and a transient fetch
    error serves the last-known-good snapshot instead of failing the page."""

    def __init__(self, min_interval):
        self.min_interval = min_interval
        self.lock = threading.Lock()
        self.entries = {}

    def get(self, region, mode):
        key = (region, mode)
        with self.lock:
            entry = self.entries.get(key)
            if entry and time.monotonic() - entry["fetched_monotonic"] < self.min_interval:
                return entry

            url = feed_url(region, mode)
            etag = entry["etag"] if entry else None
            try:
                payload, new_etag = fetch(url, etag)
            except Exception as error:
                # Broad on purpose: urlopen can raise URLError, socket
                # errors, ssl errors, or http.client exceptions depending on
                # exactly how the connection failed, and none of them
                # should crash the request thread — see do_GET's --debug
                # traceback logging for the exact cause.
                if entry:
                    entry["error"] = "%s: %s" % (type(error).__name__, error)
                    return entry
                raise

            if payload is None:  # 304 Not Modified
                entry["etag"] = new_etag
                entry["fetched_monotonic"] = time.monotonic()
                entry["fetched_at"] = time.time()
                entry["error"] = None
                return entry

            entry = {
                "etag": new_etag,
                "vehicles": parse_feed(payload),
                "fetched_monotonic": time.monotonic(),
                "fetched_at": time.time(),
                "error": None,
            }
            self.entries[key] = entry
            return entry


INDEX_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Translink live vehicles</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
  html, body { height: 100%; margin: 0; font: 14px system-ui, sans-serif; }
  #map { position: absolute; top: 48px; bottom: 0; left: 0; right: 0; background: #fff; }
  #bar { height: 48px; display: flex; align-items: center; gap: 12px; padding: 0 12px;
         background: #1f2937; color: #f3f4f6; box-sizing: border-box; }
  #bar select { font: inherit; padding: 4px 6px; }
  #bar label { display: flex; align-items: center; gap: 4px; white-space: nowrap; }
  #status { margin-left: auto; opacity: 0.85; white-space: nowrap; }
  #status.error { color: #fca5a5; }
  .veh-popup div { line-height: 1.5; }
  .track-arrow { background: transparent; border: none; }
</style>
</head>
<body>
<div id="bar">
  <label>Region <select id="region"></select></label>
  <label>Mode <select id="mode">
    <option value="">All</option>
    <option value="Bus">Bus</option>
    <option value="Rail">Rail</option>
    <option value="Ferry">Ferry</option>
  </select></label>
  <label><input type="checkbox" id="hideMap"> Hide base map</label>
  <span id="status">loading…</span>
</div>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const map = L.map('map').setView([-27.47, 153.03], 11); // Brisbane; re-fit once data arrives

// Free, no-API-key tile providers, offered as a base-layer switcher (top
// right). Dark Matter in particular makes the orange tracks and blue
// markers stand out far more than plain OpenStreetMap.
const baseLayers = {
  'OpenStreetMap': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors', maxZoom: 19
  }),
  'CartoDB Positron': L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO', subdomains: 'abcd', maxZoom: 20
  }),
  'CartoDB Dark Matter': L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO', subdomains: 'abcd', maxZoom: 20
  }),
  'Esri Satellite': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri — Esri, Maxar, Earthstar Geographics', maxZoom: 19
  }),
  'OpenTopoMap': L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
    attribution: 'Map data: &copy; OpenStreetMap contributors, SRTM | Map style: &copy; OpenTopoMap (CC-BY-SA)', maxZoom: 17
  }),
};
let activeBaseLayer = baseLayers['OpenStreetMap'].addTo(map);
L.control.layers(baseLayers, null, {position: 'topright'}).addTo(map);
map.on('baselayerchange', (e) => {
  activeBaseLayer = e.layer;
  // The control just re-added this layer on its own; respect "hide base
  // map" if it's checked, so switching layers doesn't silently un-hide it.
  if (hideMapCheckbox.checked) map.removeLayer(activeBaseLayer);
});

const regionSelect = document.getElementById('region');
const modeSelect = document.getElementById('mode');
const statusEl = document.getElementById('status');
// trackLayer is added to the map before markers so marker circles always
// render on top of the polylines beneath them.
let trackLayer = L.layerGroup().addTo(map);
let markers = L.layerGroup().addTo(map);
let fittedOnce = false;
let pollTimer = null;
let refreshMs = 15000;
let baseStatusText = '';
let nextRefreshAt = 0;

// Per-vehicle trail of points seen since the browser started polling this
// region/mode — reset on region/mode change, never persisted server-side.
const trackData = new Map();
const MAX_TRACK_POINTS = 300;

function popupHtml(v) {
  return '<div class="veh-popup">' +
    '<div><b>' + (v.label || v.vehicle_id || 'vehicle') + '</b></div>' +
    '<div>route: ' + (v.route_id || '—') + '</div>' +
    '<div>trip: ' + (v.trip_id || '—') + '</div>' +
    '<div>status: ' + (v.current_status || '—') + '</div>' +
    '<div>occupancy: ' + (v.occupancy_status || '—') + '</div>' +
    (v.speed != null ? '<div>speed: ' + v.speed.toFixed(1) + ' m/s</div>' : '') +
    '</div>';
}

function updateTracks(vehicles) {
  for (const v of vehicles) {
    if (v.vehicle_id == null) continue;
    const pts = trackData.get(v.vehicle_id) || [];
    const last = pts[pts.length - 1];
    if (!last || last[0] !== v.lat || last[1] !== v.lon) {
      pts.push([v.lat, v.lon]);
      if (pts.length > MAX_TRACK_POINTS) pts.shift();
      trackData.set(v.vehicle_id, pts);
    }
  }
}

function bearingBetween(a, b) {
  const toRad = d => d * Math.PI / 180, toDeg = r => r * 180 / Math.PI;
  const lat1 = toRad(a[0]), lat2 = toRad(b[0]), dLon = toRad(b[1] - a[1]);
  const y = Math.sin(dLon) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
  return (toDeg(Math.atan2(y, x)) + 360) % 360; // compass bearing, 0 = north
}

function arrowIcon(bearingDeg) {
  const svg = '<svg width="10" height="10" viewBox="0 0 10 10" ' +
    'style="transform: rotate(' + bearingDeg + 'deg)">' +
    '<polygon points="5,0 9,9 5,7 1,9" fill="#f97316"/></svg>';
  return L.divIcon({className: 'track-arrow', html: svg, iconSize: [10, 10], iconAnchor: [5, 5]});
}

function drawTracks() {
  trackLayer.clearLayers();
  for (const pts of trackData.values()) {
    if (pts.length > 1) {
      L.polyline(pts, {color: '#f97316', weight: 2, opacity: 0.8}).addTo(trackLayer);
    }
    // Small arrow at each prior fix, pointing toward the next fix in the
    // trail — the last one points at the current position, shown by the
    // bigger blue marker drawn on top by drawMarkers().
    for (let i = 0; i < pts.length - 1; i++) {
      const bearing = bearingBetween(pts[i], pts[i + 1]);
      L.marker(pts[i], {icon: arrowIcon(bearing), interactive: false}).addTo(trackLayer);
    }
  }
}

function drawMarkers(vehicles) {
  markers.clearLayers();
  for (const v of vehicles) {
    L.circleMarker([v.lat, v.lon], {
      radius: 5, weight: 1, color: '#1d4ed8', fillColor: '#3b82f6', fillOpacity: 0.85
    }).bindPopup(popupHtml(v)).addTo(markers);
  }
}

function tickCountdown() {
  const secs = Math.max(0, Math.round((nextRefreshAt - Date.now()) / 1000));
  statusEl.textContent = baseStatusText + (baseStatusText ? ' • ' : '') +
    'next refresh in ' + secs + 's';
}
setInterval(tickCountdown, 1000);

async function loadRegions() {
  const res = await fetch('/api/regions');
  const data = await res.json();
  refreshMs = data.interval * 1000;
  for (const group of [['Official', data.official], ['Undocumented', data.undocumented]]) {
    const optgroup = document.createElement('optgroup');
    optgroup.label = group[0];
    for (const code of group[1]) {
      const opt = document.createElement('option');
      opt.value = code;
      opt.textContent = code;
      optgroup.appendChild(opt);
    }
    regionSelect.appendChild(optgroup);
  }
  regionSelect.value = data.default_region;
}

function updateModeAvailability() {
  // Mode-specific feeds only exist for SEQ.
  modeSelect.disabled = regionSelect.value !== 'SEQ';
  if (modeSelect.disabled) modeSelect.value = '';
}

async function refresh() {
  const region = regionSelect.value;
  const mode = modeSelect.value;
  const url = '/api/positions?region=' + encodeURIComponent(region) +
              (mode ? '&mode=' + encodeURIComponent(mode) : '');
  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.error) {
      baseStatusText = region + ': ' + data.error;
      statusEl.classList.add('error');
      return;
    }
    updateTracks(data.vehicles);
    drawTracks();
    drawMarkers(data.vehicles);
    if (!fittedOnce && data.vehicles.length) {
      map.fitBounds(L.latLngBounds(data.vehicles.map(v => [v.lat, v.lon])), {maxZoom: 13});
      fittedOnce = true;
    }
    const ts = new Date(data.fetched_at * 1000).toLocaleTimeString();
    baseStatusText = data.vehicles.length + ' vehicles • updated ' + ts;
    statusEl.classList.remove('error');
  } catch (err) {
    baseStatusText = 'fetch failed: ' + err;
    statusEl.classList.add('error');
  } finally {
    nextRefreshAt = Date.now() + refreshMs;
    tickCountdown();
  }
}

function restartPolling() {
  if (pollTimer) clearInterval(pollTimer);
  fittedOnce = false; // re-fit the view for the newly selected region
  trackData.clear();  // tracks are per region/mode, not comparable across a switch
  trackLayer.clearLayers();
  refresh();
  pollTimer = setInterval(refresh, refreshMs);
}

regionSelect.addEventListener('change', () => { updateModeAvailability(); restartPolling(); });
modeSelect.addEventListener('change', restartPolling);

// Toggles only the active basemap tile layer, not trackLayer/markers —
// polling and track accumulation are unaffected either way, and the
// collected lines and points stay visible (on a plain white background)
// while the tiles are off.
const hideMapCheckbox = document.getElementById('hideMap');
hideMapCheckbox.addEventListener('change', () => {
  if (hideMapCheckbox.checked) {
    map.removeLayer(activeBaseLayer);
  } else {
    activeBaseLayer.addTo(map);
  }
});

loadRegions().then(() => { updateModeAvailability(); restartPolling(); });
</script>
</body>
</html>
"""


def make_handler(cache, default_region, interval, debug=False):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            if debug:
                # BaseHTTPRequestHandler's default format, e.g.
                # 127.0.0.1 - - [18/Aug/2026 12:00:00] "GET / HTTP/1.1" 200 -
                sys.stderr.write("%s - - [%s] %s\n" % (
                    self.address_string(), self.log_date_time_string(), fmt % args))
            # else: quiet; the status bar in the page shows fetch outcomes

        def _send(self, status, body, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, obj, status=200):
            self._send(status, json.dumps(obj).encode(), "application/json")

        def do_GET(self):
            # Any uncaught exception here would otherwise crash this request
            # thread mid-response — the browser sees that as a hung or
            # empty page load with nothing in the terminal to explain why.
            # Catch it, always log the full traceback, and answer with a
            # real HTTP response instead of leaving the connection hanging.
            try:
                self._route()
            except (BrokenPipeError, ConnectionResetError):
                pass  # client navigated away / cancelled mid-response; not a bug
            except Exception as error:
                traceback.print_exc()
                try:
                    self._send_json(
                        {"error": "internal server error: %s: %s" % (
                            type(error).__name__, error)},
                        status=500)
                except Exception:
                    pass  # headers were likely already sent; nothing more to do

        def _route(self):
            parsed = urlparse(self.path)
            if debug:
                print("-> %s %s" % (self.command, self.path), file=sys.stderr)

            if parsed.path == "/":
                self._send(200, INDEX_HTML.encode(), "text/html; charset=utf-8")
                return

            if parsed.path == "/api/regions":
                self._send_json({
                    "official": OFFICIAL_REGIONS,
                    "undocumented": UNDOCUMENTED_REGIONS,
                    "modes": MODES,
                    "default_region": default_region,
                    "interval": interval,
                })
                return

            if parsed.path == "/api/positions":
                query = parse_qs(parsed.query)
                region = query.get("region", [default_region])[0]
                mode = query.get("mode", [None])[0] or None
                if region not in ALL_REGIONS:
                    self._send_json({"error": "unknown region %r" % region}, status=400)
                    return
                if mode and mode not in MODES:
                    self._send_json({"error": "unknown mode %r" % mode}, status=400)
                    return
                if mode and region != "SEQ":
                    self._send_json(
                        {"error": "mode-specific feeds are only published for SEQ"},
                        status=400)
                    return
                try:
                    entry = cache.get(region, mode)
                except Exception as error:
                    if debug:
                        traceback.print_exc()
                    self._send_json(
                        {"error": "%s: %s" % (type(error).__name__, error)},
                        status=502)
                    return
                if debug:
                    print("   region=%s mode=%s -> %d vehicles%s" % (
                        region, mode, len(entry.get("vehicles", [])),
                        " (error: %s)" % entry["error"] if entry.get("error") else ""),
                        file=sys.stderr)
                self._send_json({
                    "vehicles": entry.get("vehicles", []),
                    "fetched_at": entry["fetched_at"],
                    "error": entry.get("error"),
                })
                return

            self._send(404, b"not found", "text/plain")

    return Handler


def main():
    parser = argparse.ArgumentParser(
        description="Local real-time map viewer for Translink vehicle "
                     "positions, with a region/mode selector in the page.")
    parser.add_argument("--host", default="127.0.0.1",
                        help="bind address (default: 127.0.0.1, localhost only)")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--region", default="SEQ", choices=ALL_REGIONS,
                        help="region selected by default when the page loads")
    parser.add_argument("--interval", type=float, default=20.0,
                        help="seconds between polls of the upstream feed, "
                             "also used as the browser's refresh interval "
                             "(default: 20)")
    parser.add_argument("--debug", action="store_true",
                        help="log every request/response and full tracebacks "
                             "for handler errors to stderr")
    args = parser.parse_args()

    if args.interval < 5:
        parser.error("interval below 5s is impolite; the feed updates slower than that")

    try:
        server = ThreadingHTTPServer((args.host, args.port),
                                     make_handler(FeedCache(min_interval=args.interval),
                                                  args.region, args.interval, args.debug))
    except OSError as error:
        # Most commonly: another process (maybe a stale earlier run of this
        # same script) already has --port bound. --debug won't help here —
        # the server never started — so spell it out directly.
        print("failed to bind http://%s:%d — %s" % (args.host, args.port, error),
              file=sys.stderr)
        print("(if this is a stale copy of viewer.py still running, find it "
              "with `lsof -i :%d` and stop it, or pass a different --port)"
              % args.port, file=sys.stderr)
        return 1

    print("serving http://%s:%d  (Ctrl+C to stop)%s" % (
        args.host, args.port, "  [debug logging on]" if args.debug else ""))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
    return 0


if __name__ == "__main__":
    sys.exit(main())
