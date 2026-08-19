#!/usr/bin/env python
"""Local map viewer for vehicle positions stored in the Parquet dataset.

Same page and HTTP API shape as viewer.py, but instead of polling the
live Translink feed, each poll re-queries the local Parquet dataset built
by translink_parquet.py for each vehicle's latest stored fix. Run this
alongside a running translink_parquet.py collector to watch its output
fill in without putting extra load on the upstream feed — or point it at
an old dataset to replay what was collected.

Mode filtering (Bus/Rail/Ferry) only works for rows translink_parquet.py
collected with a matching --mode — mode isn't part of the GTFS-RT payload,
so any row collected without --mode has no mode recorded and won't match
a mode filter here. For a one-shot GeoJSON export instead of a live page,
see current_positions.py.

Requires: pip install duckdb

Usage:
    ./viewer_parquet.py                          # http://127.0.0.1:8766, refresh every 20s
    ./viewer_parquet.py --root positions --port 9001
    ./viewer_parquet.py --max-age 300            # only vehicles seen in the last 5 min
"""

import argparse
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import duckdb

OFFICIAL_REGIONS = ("SEQ", "CNS", "NSI", "MHB", "BOW")
UNDOCUMENTED_REGIONS = ("BUN", "GLT", "GYM", "INN", "KIL", "MKY", "MAG", "MAL",
                        "RKY", "TWB", "TSV", "WAR", "WHT")
ALL_REGIONS = OFFICIAL_REGIONS + UNDOCUMENTED_REGIONS
MODES = ("Bus", "Rail", "Tram", "Ferry")

POSITIONS_QUERY = """
WITH deduped AS (
    SELECT * EXCLUDE (rn) FROM (
        SELECT *, row_number() OVER (PARTITION BY vehicle_id, ts) AS rn
        FROM read_parquet('{glob}', hive_partitioning = true)
        WHERE lat IS NOT NULL AND region = '{region}' {mode_filter}
    ) WHERE rn = 1
),
latest AS (
    SELECT *, row_number() OVER (PARTITION BY vehicle_id ORDER BY ts DESC) AS rn2
    FROM deduped
)
SELECT
    vehicle_id,
    vehicle_label AS label,
    trip_id,
    route_id,
    lat,
    lon,
    bearing,
    speed,
    current_status,
    occupancy_status,
    epoch(ts)::BIGINT AS ts
FROM latest
WHERE rn2 = 1 {age_filter}
ORDER BY vehicle_id
"""


class ParquetCache:
    """Caches the "latest known fix per vehicle" query per region so
    frequent browser polls don't rescan the Parquet dataset more often
    than --interval. Mirrors FeedCache's role in viewer.py, but the
    upstream here is local files, not a network fetch — so on error it
    also serves the last-known-good snapshot rather than failing the page."""

    def __init__(self, root, min_interval, max_age=None):
        self.glob = os.path.join(root, "**", "*.parquet")
        self.min_interval = min_interval
        self.age_filter = (" AND ts >= now() - to_seconds(%d)" % max_age
                           if max_age else "")
        self.lock = threading.Lock()
        self.entries = {}
        self.connection = duckdb.connect()

    def get(self, region, mode):
        key = (region, mode)
        with self.lock:
            entry = self.entries.get(key)
            if entry and time.monotonic() - entry["fetched_monotonic"] < self.min_interval:
                return entry

            mode_filter = " AND mode = '%s'" % mode if mode else ""
            sql = POSITIONS_QUERY.format(glob=self.glob, region=region,
                                         mode_filter=mode_filter,
                                         age_filter=self.age_filter)
            try:
                relation = self.connection.sql(sql)
                vehicles = [dict(zip(relation.columns, row))
                           for row in relation.fetchall()]
                error = None
            except Exception as exc:  # bad/missing dataset, corrupt file, etc.
                if entry:
                    entry["error"] = str(exc)
                    return entry
                vehicles, error = [], str(exc)

            entry = {
                "vehicles": vehicles,
                "fetched_monotonic": time.monotonic(),
                "fetched_at": time.time(),
                "error": error,
            }
            self.entries[key] = entry
            return entry


INDEX_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Translink stored vehicles</title>
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
let refreshMs = 20000;
let baseStatusText = '';
let nextRefreshAt = 0;

// Per-vehicle trail of points seen since the browser started polling this
// region — reset on region change, never persisted server-side.
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
    '<div>last fix: ' + (v.ts ? new Date(v.ts * 1000).toLocaleString() : '—') + '</div>' +
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
  // Mode-specific feeds only exist for SEQ, and even then only match rows
  // translink_parquet.py actually collected with that --mode.
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
  fittedOnce = false; // re-fit the view for the newly selected region/mode
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


def make_handler(cache, default_region, interval):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # quiet; the status bar in the page shows fetch outcomes

        def _send(self, status, body, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, obj, status=200):
            self._send(status, json.dumps(obj).encode(), "application/json")

        def do_GET(self):
            parsed = urlparse(self.path)

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
                entry = cache.get(region, mode)
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
        description="Local map viewer for vehicle positions stored in the "
                     "Parquet dataset built by translink_parquet.py, with a "
                     "region selector in the page. Same API shape as "
                     "viewer.py, but reads local files instead of the live feed.")
    parser.add_argument("--host", default="127.0.0.1",
                        help="bind address (default: 127.0.0.1, localhost only)")
    parser.add_argument("--port", type=int, default=8766,
                        help="default: 8766 (viewer.py defaults to 8765, so "
                             "both can run at once)")
    parser.add_argument("--root", default="positions",
                        help="Parquet dataset root directory (default: positions)")
    parser.add_argument("--region", default="SEQ", choices=ALL_REGIONS,
                        help="region selected by default when the page loads")
    parser.add_argument("--interval", type=float, default=20.0,
                        help="seconds between dataset rescans, also used as "
                             "the browser's refresh interval (default: 20)")
    parser.add_argument("--max-age", type=float,
                        help="drop vehicles whose latest stored fix is older "
                             "than this many seconds (default: no limit — "
                             "shows the true latest fix even if stale)")
    args = parser.parse_args()

    if args.interval <= 0:
        parser.error("interval must be positive")

    if not os.path.isdir(args.root):
        print("warning: %r does not exist yet — run translink_parquet.py "
              "first, or pass --root" % args.root, file=sys.stderr)

    cache = ParquetCache(args.root, min_interval=args.interval, max_age=args.max_age)
    handler = make_handler(cache, args.region, args.interval)
    server = ThreadingHTTPServer((args.host, args.port), handler)

    print("serving http://%s:%d  (Ctrl+C to stop)" % (args.host, args.port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
    return 0


if __name__ == "__main__":
    sys.exit(main())
