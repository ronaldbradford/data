
LOAD spatial;

CREATE OR REPLACE VIEW positions AS
SELECT * EXCLUDE (rn) FROM (
    SELECT *, row_number() OVER (PARTITION BY vehicle_id, ts) AS rn
    FROM read_parquet('positions/**/*.parquet', hive_partitioning = true)
) WHERE rn = 1;

CREATE OR REPLACE VIEW steps AS
SELECT *,
       ST_Distance_Sphere(ST_Point(prev_lon, prev_lat), ST_Point(lon, lat)) AS step_m,
       epoch(ts - prev_ts) AS step_s
FROM (
    SELECT *,
           lag(lat) OVER w AS prev_lat,
           lag(lon) OVER w AS prev_lon,
           lag(ts)  OVER w AS prev_ts
    FROM positions
    WHERE trip_id IS NOT NULL AND lat IS NOT NULL
    WINDOW w AS (PARTITION BY vehicle_id, trip_id ORDER BY ts)
);

SELECT trip_id, route_id, vehicle_id,
       count(*) AS points,
       round(sum(step_m) / 1000.0, 2) AS km,
       round(epoch(max(ts) - min(ts)) / 60.0, 1) AS mins,
       round(sum(step_m) / nullif(epoch(max(ts) - min(ts)), 0) * 3.6, 1) AS avg_kmh
FROM steps GROUP BY ALL ORDER BY km DESC LIMIT 20;



WITH recent AS (
    SELECT * FROM positions
    WHERE ts >= now() - INTERVAL 60 MINUTE
      AND lat IS NOT NULL
      AND route_id IS NOT NULL
), stepped AS (
    SELECT *,
           ST_Distance_Sphere(ST_Point(lag(lon) OVER w, lag(lat) OVER w),
                              ST_Point(lon, lat)) AS step_m
    FROM recent
    WINDOW w AS (PARTITION BY vehicle_id, trip_id ORDER BY ts)
)
SELECT route_id,
       count(DISTINCT vehicle_id) AS vehicles,
       count(DISTINCT trip_id)    AS trips,
       count(*)                   AS fixes,
       round(sum(step_m) / 1000.0, 1) AS km,
       strftime(max(ts) AT TIME ZONE 'Australia/Brisbane', '%H:%M:%S') AS last_seen
FROM stepped
GROUP BY route_id
ORDER BY vehicles DESC, km DESC;


/* Staleness */
SELECT strftime(max(ts) AT TIME ZONE 'Australia/Brisbane', '%Y-%m-%d %H:%M:%S') AS newest,
       round(epoch(now() - max(ts)) / 60.0, 1) AS minutes_old
FROM positions;



WITH stepped AS (
    SELECT *,
           ST_Distance_Sphere(ST_Point(lag(lon) OVER w, lag(lat) OVER w),
                              ST_Point(lon, lat)) AS step_m
    FROM positions
    WHERE split_part(route_id, '-', 1) = '608'
      AND lat IS NOT NULL
      AND trip_id IS NOT NULL
    WINDOW w AS (PARTITION BY vehicle_id, trip_id ORDER BY ts)
)
SELECT route_id, trip_id, vehicle_id,
       count(*) AS fixes,
       round(sum(step_m) / 1000.0, 2) AS km,
       strftime(min(ts) AT TIME ZONE 'Australia/Brisbane', '%H:%M') AS started,
       strftime(max(ts) AT TIME ZONE 'Australia/Brisbane', '%H:%M') AS ended
FROM stepped
GROUP BY ALL
ORDER BY started;


SELECT ts AT TIME ZONE 'Australia/Brisbane' AS ts_bne,
         lat, lon, bearing, speed, stop_id, current_status
  FROM positions
  WHERE split_part(route_id, '-', 1) = '608'
    AND trip_id = '38158270-SUN 26_27-43550' ORDER BY ts;


COPY (
  SELECT trip_id, route_id,
         ST_MakeLine(list(ST_Point(lon, lat) ORDER BY ts)) AS geom
  FROM positions
  WHERE split_part(route_id, '-', 1) = '608' AND lat IS NOT NULL
  GROUP BY trip_id, route_id
  HAVING count(*) > 5
) TO 'route608.geojson' WITH (FORMAT GDAL, DRIVER 'GeoJSON');

COPY (
  SELECT trip_id, route_id,
         ST_MakeLine(list(ST_Point(lon, lat) ORDER BY ts)) AS geom
  FROM positions
  WHERE split_part(route_id, '-', 1) = '608' AND lat IS NOT NULL
  AND trip_id = '38158270-SUN 26_27-43550'
  GROUP BY trip_id, route_id
) TO 'route608-A.geojson' WITH (FORMAT GDAL, DRIVER 'GeoJSON');

COPY (
  SELECT trip_id, route_id,
         ST_MakeLine(list(ST_Point(lon, lat) ORDER BY ts)) AS geom
  FROM positions
  WHERE split_part(route_id, '-', 1) = '539' AND lat IS NOT NULL
  GROUP BY trip_id, route_id
  HAVING count(*) > 5
) TO 'route539.geojson' WITH (FORMAT GDAL, DRIVER 'GeoJSON');



INSTALL spatial; LOAD spatial;

COPY (
    WITH deduped AS (
        SELECT * EXCLUDE (rn) FROM (
            SELECT *, row_number() OVER (PARTITION BY vehicle_id, ts) AS rn
            FROM positions
            WHERE split_part(route_id, '-', 1) = '608' AND lat IS NOT NULL
        ) WHERE rn = 1
    ),
    gapped AS (
        SELECT *,
               epoch(ts - lag(ts) OVER (PARTITION BY trip_id ORDER BY ts)) AS gap_s
        FROM deduped
    ),
    segmented AS (
        SELECT *,
               sum(CASE WHEN gap_s > 180 THEN 1 ELSE 0 END)
                   OVER (PARTITION BY trip_id ORDER BY ts
                         ROWS UNBOUNDED PRECEDING)::INTEGER AS segment_id
        FROM gapped
    )
    SELECT trip_id, route_id,
           ST_MakeLine(list(ST_Point(lon, lat) ORDER BY ts)) AS geom
    FROM segmented
    GROUP BY trip_id, route_id, segment_id
    HAVING count(*) > 5
) TO 'route608.geojson' WITH (FORMAT GDAL, DRIVER 'GeoJSON');

