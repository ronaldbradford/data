# Maps

Cameroon (`CM`) point-map experiments built from the `location` MySQL sandbox
database, generated 2026-08-15. All files below live in this directory
unless noted otherwise.

## Data sources

| Source | Used for | License / attribution |
|---|---|---|
| `place` table, `location` DB (MySQL sandbox `msb_8_4_8`) | Place points — reverse-geocoded from OpenStreetMap Nominatim, stored as JSON (`name` column: `lat`, `lon`, `address.*`, `display_name`, ...) | © OpenStreetMap contributors, ODbL 1.0 |
| [geoBoundaries](https://www.geoboundaries.org) API, `CMR` / `ADM0` | Cameroon's national boundary polygon | © geoBoundaries, Wikimedia — CC BY 3.0 |

## Local data extracts

| File | Size | Contents |
|---|---|---|
| `cm.geojson` | 56 KB | `FeatureCollection` of 235 `Point` features — every `place` row where `country_code = 'cm'`, exported via a `JSON_OBJECT`/`JSON_ARRAYAGG` query. Properties: `place_id`, `display_name`, `city`, `country_code`. |
| `cameroon-boundary.geojson` | 51 KB | `FeatureCollection` (1 `Polygon`, 1,407 vertices) — Cameroon's ADM0 boundary, downloaded from geoBoundaries' `gjDownloadURL` (simplified geometry). |

## HTML pages (Leaflet 1.9.4, self-authored dark "blueprint" theme)

All three inline the Leaflet library itself, so none depend on a CDN.

| File | Size | Basemap | Data layers | Needs network? |
|---|---|---|---|---|
| `cm-places.html` | 225 KB | None — hand-drawn 1°/5° graticule + dashed data bbox, since tile servers are unreachable from the Artifact sandbox | `cm.geojson` (points) | No |
| `cm-places-tiles.html` | 224 KB | Live CARTO Dark Matter raster tiles | `cm.geojson` (points) + dashed data bbox | Yes — fetches basemap tiles at runtime |
| `cm-places-boundary.html` | 265 KB | None — real Cameroon boundary polygon stands in for a basemap | `cm.geojson` (points) + `cameroon-boundary.geojson` (boundary) + dashed data bbox | No |

Common design: navy/amber "survey chart" palette, header panel with live
stats (feature count, named-city count, lat/lon range), legend panel,
click-to-inspect popups on every place marker.

## Published artifact

- **Cameroon Place Points** — https://claude.ai/code/artifact/fc345bd0-4fa7-464f-85ae-7c02b8c13eb7
  — the published version of `cm-places.html` (graticule, no basemap, no
  network calls — the only variant that satisfies the Artifact sandbox's
  CSP). Private by default; share from the page's share menu if needed.
- `cm-places-tiles.html` and `cm-places-boundary.html` have not been
  published as artifacts. The tiles version can't be (its basemap requests
  would be blocked by the sandbox CSP); the boundary version makes no
  network calls and could be published on request.
