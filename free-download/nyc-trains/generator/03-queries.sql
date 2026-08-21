-- Example queries against nyc_trains.position — a GeoJSON FeatureCollection
-- per row (see 02-tables.sql). Not part of the automatic
-- docker-entrypoint-initdb.d sequence — docker-compose.yml only mounts
-- 01-schema.sql/02-tables.sql, so this file is a reference/scratch pad,
-- not schema provisioning. Run it (or paste pieces of it) via:
--   docker compose exec -T mysql mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" < 03-queries.sql
-- or interactively via ../test/e2e-test.sh sql.

USE nyc_trains;

-- =============================================================================
-- 1. Flatten every feature in every snapshot into one row per train, via
--    JSON_TABLE (MySQL 8.0+). This is the workhorse everything below builds
--    on — worth keeping as a view rather than repeating the JSON_TABLE
--    clause in every query.
-- =============================================================================
CREATE OR REPLACE VIEW nyc_trains_flat AS
SELECT
  t.id           AS snapshot_id,
  t.generated_at AS snapshot_at,
  t.line         AS feed_line,
  f.trip_id, f.route_id, f.route_name, f.route_long_name, f.route_color,
  f.start_date, f.stop_id, f.stop_name, f.direction, f.status,
  f.ts, f.updated_at, f.lon, f.lat
FROM nyc_trains t,
JSON_TABLE(
  t.position, '$.features[*]'
  COLUMNS (
    trip_id         VARCHAR(64)  PATH '$.properties.trip_id',
    route_id        VARCHAR(20)  PATH '$.properties.route_id',
    route_name      VARCHAR(20)  PATH '$.properties.route_name',
    route_long_name VARCHAR(120) PATH '$.properties.route_long_name',
    route_color     CHAR(7)      PATH '$.properties.route_color',
    start_date      CHAR(8)      PATH '$.properties.start_date',
    stop_id         VARCHAR(20)  PATH '$.properties.stop_id',
    stop_name       VARCHAR(100) PATH '$.properties.stop_name',
    direction       VARCHAR(30)  PATH '$.properties.direction',
    status          VARCHAR(20)  PATH '$.properties.status',
    ts              BIGINT       PATH '$.properties.ts',
    updated_at      VARCHAR(30)  PATH '$.properties.updated',
    lon             DOUBLE       PATH '$.geometry.coordinates[0]',
    lat             DOUBLE       PATH '$.geometry.coordinates[1]'
  )
) AS f;

SELECT * FROM nyc_trains_flat ORDER BY snapshot_id DESC LIMIT 5;

-- =============================================================================
-- 2. Sanity check: does train_count match the actual feature count, and is
--    every row's JSON well-formed? (same checks ../test/e2e-test.sh runs)
-- =============================================================================
SELECT id, line, train_count, JSON_LENGTH(position, '$.features') AS actual_count,
       JSON_VALID(position) AS json_valid
FROM nyc_trains
WHERE train_count <> JSON_LENGTH(position, '$.features') OR NOT JSON_VALID(position);
-- (empty result = all good)

-- =============================================================================
-- 3. Latest snapshot per line, flattened to one row per currently-known train.
-- =============================================================================
SELECT f.*
FROM nyc_trains_flat f
JOIN (SELECT line, MAX(id) AS latest_id FROM nyc_trains GROUP BY line) latest
  ON latest.latest_id = f.snapshot_id
ORDER BY f.feed_line, f.route_id, f.stop_name;

-- =============================================================================
-- 4. Train counts by status, latest snapshot per line only.
-- =============================================================================
SELECT f.feed_line, f.status, COUNT(*) AS trains
FROM nyc_trains_flat f
JOIN (SELECT line, MAX(id) AS latest_id FROM nyc_trains GROUP BY line) latest
  ON latest.latest_id = f.snapshot_id
GROUP BY f.feed_line, f.status
ORDER BY f.feed_line, f.status;

-- =============================================================================
-- 5. Every train currently at (or approaching) a specific station — swap in
--    a real stop_name and line for your data (see query 1's output).
-- =============================================================================
SELECT feed_line, route_id, trip_id, direction, status, snapshot_at
FROM nyc_trains_flat
WHERE stop_name = 'Grand Central'
  AND snapshot_id = (SELECT MAX(id) FROM nyc_trains WHERE line = 'MNR');

-- =============================================================================
-- 6. Track one trip's movement across snapshots — swap in a real trip_id
--    (see query 1's output; PATH/subway trip_id values churn between runs
--    of generator.py, so pick one currently in your own data).
-- =============================================================================
SELECT snapshot_at, stop_name, status, lat, lon
FROM nyc_trains_flat
WHERE trip_id = 'REPLACE_ME'
ORDER BY snapshot_at;

-- =============================================================================
-- 7. Busiest stations by distinct trains seen, across everything stored.
-- =============================================================================
SELECT feed_line, stop_name, COUNT(DISTINCT trip_id) AS distinct_trains_seen
FROM nyc_trains_flat
WHERE stop_name IS NOT NULL
GROUP BY feed_line, stop_name
ORDER BY distinct_trains_seen DESC
LIMIT 20;

-- =============================================================================
-- 8. Snapshot cadence / staleness: how long ago was each line last updated?
-- =============================================================================
SELECT line, MAX(generated_at) AS last_snapshot,
       TIMESTAMPDIFF(SECOND, MAX(generated_at), UTC_TIMESTAMP(6)) AS seconds_ago
FROM nyc_trains
GROUP BY line
ORDER BY seconds_ago DESC;

-- =============================================================================
-- 9. Re-derive a GeoJSON FeatureCollection straight from SQL — e.g. one
--    line's latest snapshot filtered to only STOPPED_AT trains, for a
--    map tool that reads it back out of the database instead of a file.
-- =============================================================================
SELECT JSON_OBJECT(
  'type', 'FeatureCollection',
  'features', JSON_ARRAYAGG(JSON_OBJECT(
    'type', 'Feature',
    'geometry', JSON_OBJECT('type', 'Point', 'coordinates', JSON_ARRAY(lon, lat)),
    'properties', JSON_OBJECT('trip_id', trip_id, 'route_id', route_id, 'status', status)
  ))
) AS geojson
FROM nyc_trains_flat
WHERE feed_line = 'SI' AND status = 'STOPPED_AT'
  AND snapshot_id = (SELECT MAX(id) FROM nyc_trains WHERE line = 'SI');

-- =============================================================================
-- 10. Without JSON_TABLE/the view at all — a quick one-off extraction for
--     exploration, e.g. pasted directly into `../test/e2e-test.sh sql`.
-- =============================================================================
SELECT
  id, line, train_count,
  JSON_UNQUOTE(JSON_EXTRACT(position, '$.features[0].properties.route_id')) AS first_route,
  JSON_UNQUOTE(JSON_EXTRACT(position, '$.features[0].properties.stop_name')) AS first_stop
FROM nyc_trains
ORDER BY id DESC
LIMIT 5;

-- =============================================================================
-- 11. Export one trip's whole history as a GeoJSON file, ready to drop into
--     geojson.io / QGIS / kepler.gl / Leaflet — a Point per snapshot, in
--     chronological order, with the same property schema generator.py's own
--     output uses (so a query result and a live generator.py snapshot are
--     interchangeable). Swap the WHERE clause for any other feed_line/
--     route_id/trip_id (see query 1's output to find one).
--
--     To write straight to a file: put just this SELECT in its own .sql
--     file (e.g. trip.sql) and run
--       docker compose exec -T mysql mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
--         --default-character-set=utf8mb4 -N -B < trip.sql > trip.geojson
--     `-N -B` matters: it strips the column header and mysql's default
--     tab-separated-output escaping, which would otherwise mangle the JSON.
-- =============================================================================
SELECT JSON_OBJECT(
  'type', 'FeatureCollection',
  'features', JSON_ARRAYAGG(feature)
)
FROM (
  SELECT JSON_OBJECT(
    'type', 'Feature',
    'geometry', JSON_OBJECT('type', 'Point', 'coordinates', JSON_ARRAY(lon, lat)),
    'properties', JSON_OBJECT(
      'line', feed_line, 'trip_id', trip_id, 'route_id', route_id,
      'route_name', route_name, 'route_long_name', route_long_name, 'route_color', route_color,
      'start_date', start_date, 'stop_id', stop_id, 'stop_name', stop_name,
      'direction', direction, 'status', status, 'ts', ts, 'updated', updated_at,
      'snapshot_at', snapshot_at
    )
  ) AS feature
  FROM nyc_trains_flat
  WHERE feed_line = '1234567S' AND route_id = '7' AND trip_id = '001150_7..S'
  ORDER BY snapshot_at
) t;

-- =============================================================================
-- 12. Same trip, as a single LineString feature instead — the path it took,
--     for a cleaner line-on-a-map visualization rather than a breadcrumb of
--     points (a map tool can render both from the same query pattern; pick
--     whichever suits the tool you're using).
-- =============================================================================
SELECT JSON_OBJECT(
  'type', 'FeatureCollection',
  'features', JSON_ARRAY(JSON_OBJECT(
    'type', 'Feature',
    'geometry', JSON_OBJECT('type', 'LineString', 'coordinates', coords),
    'properties', JSON_OBJECT('line', '1234567S', 'route_id', '7', 'trip_id', '001150_7..S')
  ))
)
FROM (
  SELECT JSON_ARRAYAGG(JSON_ARRAY(lon, lat)) AS coords
  FROM (
    SELECT lon, lat FROM nyc_trains_flat
    WHERE feed_line = '1234567S' AND route_id = '7' AND trip_id = '001150_7..S'
    ORDER BY snapshot_at
  ) p
) c;

-- =============================================================================
-- 13. Find a trip on a given feed_line/route_id that's actually moving, and
--     show just the points where it changed stations — queries 6/11/12 above
--     assume you already know a trip_id, but a trip_id picked at random (e.g.
--     the first one you see in query 1) is often one still sitting at its
--     origin the whole time it's been polled, which makes those queries
--     return the same position over and over. This finds one that's really
--     moving instead: status <> 'SCHEDULED' matters — SCHEDULED rows are a
--     predicted next-stop that ticks forward on its own before the train has
--     even started, not real movement — and LAG() collapses the repeated
--     polls at the same stop down to just the moments it changed.
-- =============================================================================
WITH moving_trip AS (
  SELECT trip_id
  FROM nyc_trains_flat
  WHERE feed_line = '1234567S' AND route_id = '7' AND status <> 'SCHEDULED'
  GROUP BY trip_id
  HAVING COUNT(DISTINCT stop_id) > 1
  ORDER BY COUNT(DISTINCT stop_id) DESC, COUNT(*) DESC
  LIMIT 1
),
ordered AS (
  SELECT f.*,
         LAG(f.stop_id) OVER (ORDER BY f.snapshot_at) AS prev_stop_id
  FROM nyc_trains_flat f
  WHERE f.feed_line = '1234567S' AND f.route_id = '7' AND f.status <> 'SCHEDULED'
    AND f.trip_id = (SELECT trip_id FROM moving_trip)
)
SELECT *
FROM ordered
WHERE prev_stop_id IS NULL OR prev_stop_id <> stop_id
ORDER BY snapshot_at;
-- Drop the final WHERE to see every poll instead of just the transitions.
