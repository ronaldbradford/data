# New South Wales RealTime Transport Data

## Setup

Get an API key from opendata.transport.nsw.gov.au and add to .env

## Collect Data

```
. .env
#export TFNSW_API_KEY=<example>
nohup ./tfnsw_collect.py --interval 15 --max-runtime 6000 &
```

## Feeds

`tfnsw_collect.py` polls these GTFS-Realtime vehicle position feeds
(`--feeds` selects which to poll; default feeds are marked below):

| Feed name | Default | URL |
| --- | --- | --- |
| buses | yes | https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/buses |
| ferries | yes | https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/ferries/sydneyferries |
| nswtrains | no | https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/nswtrains |
| lightrail_cbd | no | https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/lightrail/cbdandsoutheast |
| lightrail_newcastle | no | https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/lightrail/newcastle |
| lightrail_innerwest | no | https://api.transport.nsw.gov.au/v2/gtfs/vehiclepos/lightrail/innerwest |
| sydneytrains | yes | https://api.transport.nsw.gov.au/v2/gtfs/vehiclepos/sydneytrains |
| metro | yes | https://api.transport.nsw.gov.au/v2/gtfs/vehiclepos/metro |

Run `./tfnsw_collect.py --check` to confirm which of these your API key can
reach; TfNSW's catalogue does change.

```
$ ./tfnsw_collect.py --check
feed          status   entities  url
buses         ok       1562      https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/buses
ferries       ok       20        https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/ferries/sydneyferries
lightrail_cbd ok       18        https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/lightrail/cbdandsoutheast
lightrail_innerwest ok       9         https://api.transport.nsw.gov.au/v2/gtfs/vehiclepos/lightrail/innerwest
lightrail_newcastle ok       3         https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/lightrail/newcastle
metro         ok       24        https://api.transport.nsw.gov.au/v2/gtfs/vehiclepos/metro
nswtrains     ok       31        https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/nswtrains
sydneytrains  ok       204       https://api.transport.nsw.gov.au/v2/gtfs/vehiclepos/sydneytrains
```

## Sample Queries

The dataset is Hive-partitioned by `dt` (date) and `feed` (mode), so DuckDB
can query the whole `positions/` tree directly — pass `hive_partitioning=true`
to expose `dt` and `feed` as regular columns:

```sql
-- Row and vehicle counts per feed, today
SELECT feed, COUNT(*) AS rows, COUNT(DISTINCT vehicle_id) AS vehicles
FROM read_parquet('positions/**/*.parquet', hive_partitioning=true)
WHERE dt = current_date
GROUP BY feed
ORDER BY feed;

-- Most recent known position of every bus
SELECT vehicle_id, route_id, lat, lon, speed, ts
FROM read_parquet('positions/dt=*/feed=buses/*.parquet', hive_partitioning=true)
QUALIFY ROW_NUMBER() OVER (PARTITION BY vehicle_id ORDER BY ts DESC) = 1
ORDER BY ts DESC;

-- Busiest bus routes today, by distinct vehicles seen
SELECT route_id, COUNT(DISTINCT vehicle_id) AS vehicles
FROM read_parquet('positions/**/*.parquet', hive_partitioning=true)
WHERE feed = 'buses' AND dt = current_date AND route_id IS NOT NULL
GROUP BY route_id
ORDER BY vehicles DESC
LIMIT 10;

-- Average reported speed (km/h) by feed
SELECT feed, round(avg(speed) * 3.6, 1) AS avg_kmh
FROM read_parquet('positions/**/*.parquet', hive_partitioning=true)
WHERE speed IS NOT NULL
GROUP BY feed
ORDER BY feed;

-- Vehicle status breakdown (in transit vs. stopped at a stop) per feed
SELECT feed, current_status, COUNT(*) AS n
FROM read_parquet('positions/**/*.parquet', hive_partitioning=true)
GROUP BY feed, current_status
ORDER BY feed, n DESC;
```

Run any of these with `duckdb -c "<query>"` from this directory, or open
`duckdb` interactively and query the same `read_parquet(...)` paths.

## GeoJSON Export

`top10_bus_routes.geojson` traces one trip for each of the 10 busiest bus
routes (by distinct vehicles seen) as a `FeatureCollection` of `LineString`
geometries. For each route, the trip with the most GPS-fixed position reports
is chosen so the traced path is as complete as possible.

Generated with DuckDB's [spatial extension](https://duckdb.org/docs/extensions/spatial):

```sql
INSTALL spatial;
LOAD spatial;

COPY (
  WITH top_routes AS (
    SELECT route_id, COUNT(DISTINCT vehicle_id) AS vehicles
    FROM read_parquet('positions/**/*.parquet', hive_partitioning=true)
    WHERE feed='buses' AND route_id IS NOT NULL
    GROUP BY route_id
    ORDER BY vehicles DESC
    LIMIT 10
  ),
  trip_counts AS (
    SELECT route_id, trip_id, vehicle_id, COUNT(*) FILTER (WHERE lat IS NOT NULL) AS n_geo
    FROM read_parquet('positions/**/*.parquet', hive_partitioning=true)
    WHERE feed='buses' AND trip_id IS NOT NULL
      AND route_id IN (SELECT route_id FROM top_routes)
    GROUP BY route_id, trip_id, vehicle_id
  ),
  best_trip AS (
    SELECT route_id, trip_id, vehicle_id
    FROM trip_counts
    QUALIFY ROW_NUMBER() OVER (PARTITION BY route_id ORDER BY n_geo DESC) = 1
  ),
  points AS (
    SELECT p.route_id, p.trip_id, p.vehicle_id, p.ts, p.lat, p.lon, p.speed, p.current_status
    FROM read_parquet('positions/**/*.parquet', hive_partitioning=true) p
    JOIN best_trip b USING (route_id, trip_id, vehicle_id)
    WHERE p.feed='buses' AND p.lat IS NOT NULL AND p.lon IS NOT NULL
    ORDER BY p.ts
  ),
  lines AS (
    SELECT
      route_id, trip_id, vehicle_id,
      COUNT(*) AS point_count,
      MIN(ts) AS start_ts,
      MAX(ts) AS end_ts,
      round(avg(speed) * 3.6, 1) AS avg_kmh,
      ST_MakeLine(list(ST_Point(lon, lat) ORDER BY ts)) AS geom
    FROM points
    GROUP BY route_id, trip_id, vehicle_id
  )
  SELECT
    'Feature' AS type,
    ST_AsGeoJSON(geom)::JSON AS geometry,
    {
      route_id: route_id,
      trip_id: trip_id,
      vehicle_id: vehicle_id,
      point_count: point_count,
      start_ts: strftime(start_ts, '%Y-%m-%dT%H:%M:%S%z'),
      end_ts: strftime(end_ts, '%Y-%m-%dT%H:%M:%S%z'),
      avg_kmh: avg_kmh
    } AS properties
  FROM lines
  ORDER BY point_count DESC
) TO 'features.json' (FORMAT JSON, ARRAY true);
```

DuckDB's `COPY ... TO (FORMAT JSON, ARRAY true)` writes a bare JSON array of
Feature objects, so wrap it in a `FeatureCollection` to get valid GeoJSON:

```python
import json
features = json.load(open('features.json'))
fc = {'type': 'FeatureCollection', 'features': features}
json.dump(fc, open('top10_bus_routes.geojson', 'w'), indent=2)
```

Each feature's `properties` includes `route_id`, `trip_id`, `vehicle_id`,
`point_count`, `start_ts`/`end_ts` and `avg_kmh`:

| route_id | points | avg km/h | span |
| --- | --- | --- | --- |
| 7083_SW1 | 126 | 16.7 | 23:41–00:35 |
| 2508_B1 | 124 | 38.5 | 23:36–00:19 |
| 2503_80 | 124 | 35.7 | 23:41–00:35 |
| 7084_SW2 | 124 | 13.1 | 23:41–00:19 |
| 2459_423 | 123 | 23.9 | 23:41–00:19 |
| 2507_52 | 123 | 36.7 | 23:41–00:19 |
| 2509_390X | 108 | 30.5 | 23:38–00:16 |
| 2509_333 | 104 | 18.0 | 23:48–00:19 |
| 2509_309 | 99 | 30.6 | 23:48–00:14 |
| 2509_379 | 75 | 26.8 | 23:55–00:18 |

Open the file in [geojson.io](https://geojson.io) or any GIS tool to view the
traced paths.
