#!/usr/bin/env python
"""Local real-time map viewer for NYC-area rail: Subway, LIRR, Metro-North
and PATH.

Serves a single-page Leaflet map in the browser that polls this local
server, which in turn polls whichever *live* GTFS-Realtime feed is
selected in the page's dropdown. MTA splits its feed by line group/agency
rather than by individual route (see FEEDS below). Nothing is stored —
this is a live viewer, not a collector.

Positions generally jump station to station along the actual line rather
than following a continuous GPS trail — see ../nyc_rail.py, which this
script shares with generator/generator.py (a one-shot GeoJSON emitter of
the same data), for the full details on how a train's position is
derived.

Requires: pip install gtfs-realtime-bindings

Usage:
    ./viewer.py                          # http://127.0.0.1:8767, refresh every 20s
    ./viewer.py --port 9000 --interval 10
    ./viewer.py --host 0.0.0.0           # expose beyond localhost (e.g. LAN demo)
    ./viewer.py --refresh-static         # force re-download of station/route data
"""

import argparse
import json
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

# nyc_rail.py is shared with generator/generator.py, so it lives one
# level up rather than under either — not importable by its plain module
# name until that directory is on sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import nyc_rail  # noqa: E402

FEEDS = nyc_rail.FEEDS
FEED_GROUPS = nyc_rail.FEED_GROUPS
DEFAULT_FEED = nyc_rail.DEFAULT_FEED


class FeedCache:
    """Per-feed cache so concurrent/rapid browser polls never hit the
    upstream feed more often than --interval, and a transient fetch error
    serves the last-known-good snapshot instead of failing the page."""

    def __init__(self, min_interval, static_data):
        self.min_interval = min_interval
        self.static_data = static_data
        self.lock = threading.Lock()
        self.entries = {}

    def get(self, feed_id):
        with self.lock:
            entry = self.entries.get(feed_id)
            if entry and time.monotonic() - entry["fetched_monotonic"] < self.min_interval:
                return entry

            url = FEEDS[feed_id]["url"]
            etag = entry["etag"] if entry else None
            try:
                payload, new_etag = nyc_rail.fetch(url, etag)
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

            agency = FEEDS[feed_id]["agency"]
            stops = self.static_data[agency]["stops"]
            entry = {
                "etag": new_etag,
                "trains": nyc_rail.parse_feed(payload, stops),
                "fetched_monotonic": time.monotonic(),
                "fetched_at": time.time(),
                "error": None,
            }
            self.entries[feed_id] = entry
            return entry


INDEX_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>NYC-area rail — live trains</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
  html, body { height: 100%; margin: 0; font: 14px system-ui, sans-serif; }
  #map { position: absolute; top: 48px; bottom: 0; left: 0; right: 0; background: #fff; }
  #bar { height: 48px; display: flex; align-items: center; gap: 12px; padding: 0 12px;
         background: #1f2937; color: #f3f4f6; box-sizing: border-box; }
  #bar select, #bar input[type=text] { font: inherit; padding: 4px 6px; }
  #bar label { display: flex; align-items: center; gap: 4px; white-space: nowrap; }
  #status { margin-left: auto; opacity: 0.85; white-space: nowrap; }
  #status.error { color: #fca5a5; }
  .train-popup div { line-height: 1.5; }
  .subway-bullet { display: flex; align-items: center; justify-content: center;
                    border-radius: 50%; font: 700 11px system-ui, sans-serif;
                    border: 2px solid rgba(0,0,0,0.35); box-shadow: 0 1px 3px rgba(0,0,0,0.4); }
  .track-arrow { background: transparent; border: none; }
</style>
</head>
<body>
<div id="bar">
  <label>Line <select id="line"></select></label>
  <label>Route <input type="text" id="routeFilter" size="6" placeholder="e.g. 6 or A"
    title="Matches the selected line's route id exactly, e.g. 6 matches only the 6 train, not 6X"></label>
  <label><input type="checkbox" id="showScheduled" checked> Show scheduled (not yet positioned)</label>
  <label>History <select id="history"></select></label>
  <label><input type="checkbox" id="hideMap"> Hide base map</label>
  <span id="status">loading…</span>
</div>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const map = L.map('map').setView([40.73, -73.95], 10); // NYC; re-fit once data arrives

// Free, no-API-key tile providers, offered as a base-layer switcher (top
// right). Dark Matter in particular makes the colored line bullets stand
// out far more than plain OpenStreetMap.
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
};
let activeBaseLayer = baseLayers['OpenStreetMap'].addTo(map);
L.control.layers(baseLayers, null, {position: 'topright'}).addTo(map);
map.on('baselayerchange', (e) => {
  activeBaseLayer = e.layer;
  // The control just re-added this layer on its own; respect "hide base
  // map" if it's checked, so switching layers doesn't silently un-hide it.
  if (hideMapCheckbox.checked) map.removeLayer(activeBaseLayer);
});

const lineSelect = document.getElementById('line');
const statusEl = document.getElementById('status');
// trackLayer is added to the map before markers so bullet icons always
// render on top of the trails beneath them.
let trackLayer = L.layerGroup().addTo(map);
let markers = L.layerGroup().addTo(map);
let fittedOnce = false;
let pollTimer = null;
let refreshMs = 15000;
let baseStatusText = '';
let nextRefreshAt = 0;
let routesByLine = {}; // line -> {route_id: {color, text_color, name, long_name}}, from /api/lines

const routeFilterInput = document.getElementById('routeFilter');
const showScheduledCheckbox = document.getElementById('showScheduled');
routeFilterInput.addEventListener('input', render);
showScheduledCheckbox.addEventListener('change', render);

// Per-trip trail of stations seen since the browser started polling this
// line — reset on line change, never persisted server-side. Each entry
// jumps station to station (most of these feeds have no continuous GPS),
// so trails follow the actual track rather than a smooth path.
const trackData = new Map(); // trip_id -> {color, points: [[lat,lon], ...]}
const historySelect = document.getElementById('history');
for (let n = 5; n <= 50; n += 5) {
  const opt = document.createElement('option');
  opt.value = n;
  opt.textContent = n;
  historySelect.appendChild(opt);
}
historySelect.value = 20; // default; user-selectable 5-50 in steps of 5
let maxTrackPoints = Number(historySelect.value);

function trimTracks() {
  // Applies a lowered history length immediately, rather than waiting for
  // enough future pushes to shift each trail down one point at a time.
  for (const [id, entry] of trackData) {
    if (entry.points.length > maxTrackPoints) entry.points = entry.points.slice(-maxTrackPoints);
  }
}
historySelect.addEventListener('change', () => {
  maxTrackPoints = Number(historySelect.value);
  trimTracks();
  render();
});

function matchesFilters(v) {
  const filter = routeFilterInput.value.trim();
  if (filter && v.route_id !== filter) return false;
  if (!showScheduledCheckbox.checked && v.status === 'SCHEDULED') return false;
  return true;
}

function routeInfo(routeId) {
  const table = routesByLine[lineSelect.value] || {};
  return table[routeId] || {color: '6E6E6E', text_color: 'FFFFFF', name: routeId || '?', long_name: routeId || 'unknown route'};
}

function popupHtml(v) {
  const info = routeInfo(v.route_id);
  return '<div class="train-popup">' +
    '<div><b>' + info.name + '</b>' + (info.long_name && info.long_name !== info.name ? ' — ' + info.long_name : '') +
      (v.direction ? ' • ' + v.direction : '') + '</div>' +
    '<div>status: ' + v.status + '</div>' +
    '<div>' + (v.status === 'SCHEDULED' ? 'next stop: ' : 'stop: ') + (v.stop_name || v.stop_id || '—') + '</div>' +
    '<div>trip: ' + v.trip_id + '</div>' +
    (v.ts ? '<div>updated: ' + new Date(v.ts * 1000).toLocaleTimeString() + '</div>' : '') +
    '</div>';
}

function updateTracks(trains) {
  for (const v of trains) {
    if (v.trip_id == null) continue;
    const info = routeInfo(v.route_id);
    const entry = trackData.get(v.trip_id) || {color: info.color, points: []};
    entry.color = info.color; // keep in sync in case route_id ever changes mid-trip
    const pts = entry.points;
    const last = pts[pts.length - 1];
    if (!last || last[0] !== v.lat || last[1] !== v.lon) {
      pts.push([v.lat, v.lon]);
      if (pts.length > maxTrackPoints) pts.shift();
    }
    trackData.set(v.trip_id, entry);
  }
}

function bearingBetween(a, b) {
  const toRad = d => d * Math.PI / 180, toDeg = r => r * 180 / Math.PI;
  const lat1 = toRad(a[0]), lat2 = toRad(b[0]), dLon = toRad(b[1] - a[1]);
  const y = Math.sin(dLon) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
  return (toDeg(Math.atan2(y, x)) + 360) % 360; // compass bearing, 0 = north
}

function arrowIcon(bearingDeg, color) {
  const svg = '<svg width="10" height="10" viewBox="0 0 10 10" ' +
    'style="transform: rotate(' + bearingDeg + 'deg)">' +
    '<polygon points="5,0 9,9 5,7 1,9" fill="#' + color + '"/></svg>';
  return L.divIcon({className: 'track-arrow', html: svg, iconSize: [10, 10], iconAnchor: [5, 5]});
}

function drawTracks(visibleIds) {
  trackLayer.clearLayers();
  for (const [id, entry] of trackData) {
    if (visibleIds && !visibleIds.has(id)) continue;
    const pts = entry.points;
    if (pts.length > 1) {
      L.polyline(pts, {color: '#' + entry.color, weight: 3, opacity: 0.8}).addTo(trackLayer);
    }
    // Small arrow at each prior fix, pointing toward the next station in
    // the trail — the last one points at the current position, shown by
    // the bullet icon drawn on top by drawMarkers().
    for (let i = 0; i < pts.length - 1; i++) {
      const bearing = bearingBetween(pts[i], pts[i + 1]);
      L.marker(pts[i], {icon: arrowIcon(bearing, entry.color), interactive: false}).addTo(trackLayer);
    }
  }
}

function bulletIcon(v) {
  const info = routeInfo(v.route_id);
  const faded = v.status === 'SCHEDULED';
  const style = 'width:22px;height:22px;background:#' + info.color + ';color:#' + info.text_color +
    ';opacity:' + (faded ? 0.55 : 1) + (faded ? ';border-style:dashed' : '') + ';';
  const html = '<div class="subway-bullet" style="' + style + '">' + info.name + '</div>';
  return L.divIcon({className: '', html, iconSize: [22, 22], iconAnchor: [11, 11]});
}

function drawMarkers(trains) {
  markers.clearLayers();
  for (const v of trains) {
    L.marker([v.lat, v.lon], {icon: bulletIcon(v)}).bindPopup(popupHtml(v)).addTo(markers);
  }
}

function tickCountdown() {
  const secs = Math.max(0, Math.round((nextRefreshAt - Date.now()) / 1000));
  statusEl.textContent = baseStatusText + (baseStatusText ? ' • ' : '') +
    'next refresh in ' + secs + 's';
}
setInterval(tickCountdown, 1000);

async function loadLines() {
  const res = await fetch('/api/lines');
  const data = await res.json();
  refreshMs = data.interval * 1000;
  routesByLine = data.routes;
  for (const [label, codes] of data.groups) {
    const optgroup = document.createElement('optgroup');
    optgroup.label = label;
    for (const code of codes) {
      const opt = document.createElement('option');
      opt.value = code;
      opt.textContent = code;
      optgroup.appendChild(opt);
    }
    lineSelect.appendChild(optgroup);
  }
  lineSelect.value = data.default_feed;
}

let lastTrains = [];
let lastFetchedAt = 0;

// Draws the current lastTrains/trackData, applying the active filters —
// separate from refresh() so the Route input and History dropdown can
// re-render instantly against already-fetched data, with no need to wait
// for (or force) another poll.
function render() {
  const visible = lastTrains.filter(matchesFilters);
  const visibleIds = new Set(visible.map(v => v.trip_id));
  drawTracks(visibleIds);
  drawMarkers(visible);
  if (!fittedOnce && visible.length) {
    map.fitBounds(L.latLngBounds(visible.map(v => [v.lat, v.lon])), {maxZoom: 13});
    fittedOnce = true;
  }
  if (lastFetchedAt) {
    const ts = new Date(lastFetchedAt * 1000).toLocaleTimeString();
    const countText = visible.length === lastTrains.length
      ? String(visible.length)
      : visible.length + ' of ' + lastTrains.length;
    baseStatusText = countText + ' trains • updated ' + ts;
    statusEl.classList.remove('error');
  }
}

async function refresh() {
  const line = lineSelect.value;
  const url = '/api/positions?line=' + encodeURIComponent(line);
  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.error) {
      baseStatusText = line + ': ' + data.error;
      statusEl.classList.add('error');
      return;
    }
    updateTracks(data.trains); // tracks every train, regardless of the active filters
    lastTrains = data.trains;
    lastFetchedAt = data.fetched_at;
    render();
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
  fittedOnce = false; // re-fit the view for the newly selected line
  trackData.clear();  // tracks are per line, not comparable across a switch
  trackLayer.clearLayers();
  refresh();
  pollTimer = setInterval(refresh, refreshMs);
}

lineSelect.addEventListener('change', restartPolling);

// Toggles only the active basemap tile layer, not trackLayer/markers —
// polling and track accumulation are unaffected either way, and the
// collected lines and bullets stay visible (on a plain white background)
// while the tiles are off.
const hideMapCheckbox = document.getElementById('hideMap');
hideMapCheckbox.addEventListener('change', () => {
  if (hideMapCheckbox.checked) {
    map.removeLayer(activeBaseLayer);
  } else {
    activeBaseLayer.addTo(map);
  }
});

loadLines().then(restartPolling);
</script>
</body>
</html>
"""


def make_handler(cache, default_feed, interval, routes_by_line, debug=False):
    lines_payload = json.dumps({
        "groups": FEED_GROUPS,
        "default_feed": default_feed,
        "interval": interval,
        "routes": routes_by_line,
    }).encode()

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

            if parsed.path == "/api/lines":
                self._send(200, lines_payload, "application/json")
                return

            if parsed.path == "/api/positions":
                query = parse_qs(parsed.query)
                feed_id = query.get("line", [default_feed])[0]
                if feed_id not in FEEDS:
                    self._send_json({"error": "unknown line %r" % feed_id}, status=400)
                    return
                try:
                    entry = cache.get(feed_id)
                except Exception as error:
                    if debug:
                        traceback.print_exc()
                    self._send_json(
                        {"error": "%s: %s" % (type(error).__name__, error)},
                        status=502)
                    return
                if debug:
                    print("   line=%s -> %d trains%s" % (
                        feed_id, len(entry.get("trains", [])),
                        " (error: %s)" % entry["error"] if entry.get("error") else ""),
                        file=sys.stderr)
                self._send_json({
                    "trains": entry.get("trains", []),
                    "fetched_at": entry["fetched_at"],
                    "error": entry.get("error"),
                })
                return

            self._send(404, b"not found", "text/plain")

    return Handler


def main():
    parser = argparse.ArgumentParser(
        description="Local real-time map viewer for NYC-area rail (Subway, "
                     "LIRR, Metro-North, PATH), with a line/route selector "
                     "in the page.")
    parser.add_argument("--host", default="127.0.0.1",
                        help="bind address (default: 127.0.0.1, localhost only)")
    parser.add_argument("--port", type=int, default=8767,
                        help="default: 8767 (8765/8766 are used by the "
                             "queensland-transport viewers)")
    parser.add_argument("--line", default=DEFAULT_FEED, choices=sorted(FEEDS),
                        help="line group selected by default when the page loads")
    parser.add_argument("--interval", type=float, default=20.0,
                        help="seconds between polls of the upstream feed, "
                             "also used as the browser's refresh interval "
                             "(default: 20)")
    parser.add_argument("--refresh-static", action="store_true",
                        help="force re-download of station locations/route "
                             "colors instead of using the on-disk cache")
    parser.add_argument("--debug", action="store_true",
                        help="log every request/response and full tracebacks "
                             "for handler errors to stderr")
    args = parser.parse_args()

    if args.interval < 5:
        parser.error("interval below 5s is impolite; the feed updates slower than that")

    print("loading station locations and route colors...", file=sys.stderr)
    try:
        static_data = nyc_rail.load_static_data(force_refresh=args.refresh_static)
    except Exception as error:
        print("failed to load static GTFS data: %s: %s" % (
            type(error).__name__, error), file=sys.stderr)
        return 1

    routes_by_line = {feed_id: static_data[info["agency"]]["routes"]
                       for feed_id, info in FEEDS.items()}

    try:
        server = ThreadingHTTPServer(
            (args.host, args.port),
            make_handler(FeedCache(min_interval=args.interval, static_data=static_data),
                         args.line, args.interval, routes_by_line, args.debug))
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
