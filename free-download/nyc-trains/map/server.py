#!/usr/bin/env python
"""Local Leaflet map viewer for any GeoJSON file — a generic companion to
viewer/viewer.py (which is specific to the live MTA feeds) for looking at
whatever's already been generated, e.g. generator/03-queries.sql's
trip.geojson/trip-line.geojson exports, or generator.py's own output
redirected to a file.

Serves a single-page Leaflet map that reads a filename from the page's
?file= query argument (or the text box, which keeps the URL in sync), and
loads it from a small stdlib http.server backend — no Flask, no other
dependencies. Only files inside --dir are servable, matched by bare
filename with no path separators, so a URL can't walk outside it.

Usage:
    cd ../generator && ../map/server.py   # serve whatever's in generator/
    ../map/server.py --dir ../generator   # equivalently, from anywhere
    ./server.py --port 9000
    ./server.py --host 0.0.0.0            # expose beyond localhost (e.g. LAN demo)

Then open http://127.0.0.1:8768/?file=trip.geojson (or use the box on
the page — it lists every .geojson/.json file found in --dir).
"""

import argparse
import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

GEOJSON_EXTENSIONS = (".geojson", ".json")

INDEX_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>GeoJSON file viewer</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
  html, body { height: 100%; margin: 0; font: 14px system-ui, sans-serif; }
  #map { position: absolute; top: 48px; bottom: 0; left: 0; right: 0; background: #fff; }
  #bar { height: 48px; display: flex; align-items: center; gap: 8px; padding: 0 12px;
         background: #1f2937; color: #f3f4f6; box-sizing: border-box; }
  #bar input[type=text] { font: inherit; padding: 4px 6px; width: 22em; }
  #bar button { font: inherit; padding: 4px 10px; cursor: pointer; }
  #status { margin-left: auto; opacity: 0.85; white-space: nowrap; }
  #status.error { color: #fca5a5; }
  .feature-popup div { line-height: 1.5; }
</style>
</head>
<body>
<div id="bar">
  <label>File <input type="text" id="fileInput" list="fileList" placeholder="e.g. trip.geojson"></label>
  <datalist id="fileList"></datalist>
  <button id="loadBtn">Load</button>
  <label><input type="checkbox" id="hideMap"> Hide base map</label>
  <span id="status">pick a file…</span>
</div>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const map = L.map('map').setView([40.73, -73.95], 10); // NYC-ish default; fits to data once loaded

// Free, no-API-key tile providers, offered as a base-layer switcher (top
// right). Dark Matter in particular makes colored markers/lines stand
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

// Toggles only the active basemap tile layer, not the GeoJSON layer —
// the loaded data stays visible (on a plain white background) while the
// tiles are off.
const hideMapCheckbox = document.getElementById('hideMap');
hideMapCheckbox.addEventListener('change', () => {
  if (hideMapCheckbox.checked) {
    map.removeLayer(activeBaseLayer);
  } else {
    activeBaseLayer.addTo(map);
  }
});

const fileInput = document.getElementById('fileInput');
const loadBtn = document.getElementById('loadBtn');
const fileListEl = document.getElementById('fileList');
const statusEl = document.getElementById('status');
let layer = null;

// Generic styling: honor a per-feature "color"/"route_color" property
// (both #RRGGBB or bare RRGGBB) if present — e.g. generator.py's own
// GeoJSON output already carries route_color — otherwise fall back to a
// plain default so any arbitrary GeoJSON file still renders sensibly.
function featureColor(feature) {
  const raw = (feature.properties && (feature.properties.route_color || feature.properties.color)) || null;
  if (!raw) return '#3b82f6';
  return raw.startsWith('#') ? raw : '#' + raw;
}

function pointToLayer(feature, latlng) {
  return L.circleMarker(latlng, {
    radius: 6, weight: 2, color: '#1f2937', fillColor: featureColor(feature), fillOpacity: 0.85
  });
}

function styleFn(feature) {
  return { color: featureColor(feature), weight: 3, opacity: 0.85 };
}

function popupHtml(feature) {
  const props = feature.properties || {};
  const rows = Object.entries(props)
    .filter(([, v]) => v !== null && v !== undefined && v !== '')
    .map(([k, v]) => '<div><b>' + k + ':</b> ' + v + '</div>')
    .join('');
  return '<div class="feature-popup">' + (rows || '<div>(no properties)</div>') + '</div>';
}

async function loadFileList() {
  try {
    const res = await fetch('/api/files');
    const files = await res.json();
    fileListEl.innerHTML = '';
    for (const f of files) {
      const opt = document.createElement('option');
      opt.value = f;
      fileListEl.appendChild(opt);
    }
  } catch (err) {
    // Non-fatal — typing a filename by hand still works without the list.
  }
}

async function loadFile(name, updateUrl) {
  if (!name) return;
  statusEl.textContent = 'loading ' + name + '...';
  statusEl.classList.remove('error');
  try {
    const res = await fetch('/api/geojson?file=' + encodeURIComponent(name));
    if (!res.ok) {
      statusEl.textContent = name + ': ' + (await res.text());
      statusEl.classList.add('error');
      return;
    }
    const data = await res.json();
    if (layer) map.removeLayer(layer);
    layer = L.geoJSON(data, { pointToLayer, style: styleFn,
      onEachFeature: (feature, lyr) => lyr.bindPopup(popupHtml(feature)) }).addTo(map);
    const bounds = layer.getBounds();
    if (bounds.isValid()) map.fitBounds(bounds, { maxZoom: 15 });
    const count = (data.features || []).length;
    statusEl.textContent = name + ' — ' + count + ' feature' + (count === 1 ? '' : 's');
    if (updateUrl) {
      const url = new URL(location.href);
      url.searchParams.set('file', name);
      history.replaceState(null, '', url);
    }
  } catch (err) {
    statusEl.textContent = name + ': ' + err;
    statusEl.classList.add('error');
  }
}

loadBtn.addEventListener('click', () => loadFile(fileInput.value.trim(), true));
fileInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') loadFile(fileInput.value.trim(), true);
});

loadFileList().then(() => {
  const fromUrl = new URLSearchParams(location.search).get('file');
  if (fromUrl) {
    fileInput.value = fromUrl;
    loadFile(fromUrl, false);
  }
});
</script>
</body>
</html>
"""


def safe_path(root, filename):
    """Resolve filename against root, refusing anything that isn't a bare
    filename inside it (no path separators, no traversal). Returns the
    absolute path, or None if filename is unsafe or the extension isn't
    an expected GeoJSON one."""
    if not filename or os.sep in filename or (os.altsep and os.altsep in filename):
        return None
    if filename in (os.curdir, os.pardir):
        return None
    if not filename.lower().endswith(GEOJSON_EXTENSIONS):
        return None
    candidate = os.path.join(root, filename)
    resolved = os.path.realpath(candidate)
    if os.path.commonpath([resolved, root]) != root:
        return None  # symlink or similar escaping root
    return resolved


def make_handler(root, debug=False):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            if debug:
                sys.stderr.write("%s - - [%s] %s\n" % (
                    self.address_string(), self.log_date_time_string(), fmt % args))

        def _send(self, status, body, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            try:
                self._route()
            except (BrokenPipeError, ConnectionResetError):
                pass  # client navigated away mid-response; not a bug
            except Exception as error:
                traceback.print_exc()
                try:
                    self._send(500, ("internal server error: %s: %s" % (
                        type(error).__name__, error)).encode(), "text/plain")
                except Exception:
                    pass

        def _route(self):
            parsed = urlparse(self.path)
            if debug:
                print("-> %s %s" % (self.command, self.path), file=sys.stderr)

            if parsed.path == "/":
                self._send(200, INDEX_HTML.encode(), "text/html; charset=utf-8")
                return

            if parsed.path == "/api/files":
                try:
                    names = sorted(
                        name for name in os.listdir(root)
                        if name.lower().endswith(GEOJSON_EXTENSIONS)
                        and os.path.isfile(os.path.join(root, name)))
                except OSError as error:
                    self._send(500, str(error).encode(), "text/plain")
                    return
                self._send(200, json.dumps(names).encode(), "application/json")
                return

            if parsed.path == "/api/geojson":
                query = parse_qs(parsed.query)
                filename = query.get("file", [None])[0]
                path = safe_path(root, filename) if filename else None
                if path is None:
                    self._send(400, ("invalid or missing 'file' — must be a bare "
                                      "%s filename inside %s" % (
                                          "/".join(GEOJSON_EXTENSIONS), root)).encode(),
                               "text/plain")
                    return
                if not os.path.isfile(path):
                    self._send(404, ("not found: %s" % filename).encode(), "text/plain")
                    return
                try:
                    with open(path, "rb") as f:
                        body = f.read()
                except OSError as error:
                    self._send(500, str(error).encode(), "text/plain")
                    return
                self._send(200, body, "application/json")
                return

            self._send(404, b"not found", "text/plain")

    return Handler


def main():
    parser = argparse.ArgumentParser(
        description="Local Leaflet viewer for GeoJSON files, served from "
                     "a directory via a small stdlib http.server backend.")
    parser.add_argument("--host", default="127.0.0.1",
                        help="bind address (default: 127.0.0.1, localhost only)")
    parser.add_argument("--port", type=int, default=8768,
                        help="default: 8768 (8765/8766/8767 are used by the "
                             "other viewers in this repo)")
    parser.add_argument("--dir", default=".",
                        help="directory to serve .geojson/.json files from "
                             "(default: current directory)")
    parser.add_argument("--debug", action="store_true",
                        help="log every request/response and full tracebacks "
                             "for handler errors to stderr")
    args = parser.parse_args()

    root = os.path.realpath(args.dir)
    if not os.path.isdir(root):
        print("ERROR: --dir %r is not a directory" % args.dir, file=sys.stderr)
        return 1

    try:
        server = ThreadingHTTPServer((args.host, args.port), make_handler(root, args.debug))
    except OSError as error:
        print("failed to bind http://%s:%d — %s" % (args.host, args.port, error),
              file=sys.stderr)
        print("(if this is a stale copy of server.py still running, find it "
              "with `lsof -i :%d` and stop it, or pass a different --port)"
              % args.port, file=sys.stderr)
        return 1

    print("serving GeoJSON files from %s" % root)
    print("serving http://%s:%d  (Ctrl+C to stop)%s" % (
        args.host, args.port, "  [debug logging on]" if args.debug else ""))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
    return 0


if __name__ == "__main__":
    sys.exit(main())
