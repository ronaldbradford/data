WITH deltas AS (
    SELECT epoch(ts - lag(ts) OVER (PARTITION BY vehicle_id, trip_id ORDER BY ts)) AS delta_s
    FROM read_parquet('positions/**/*.parquet', hive_partitioning = true)
    WHERE trip_id IS NOT NULL
)
SELECT least(delta_s, 120) AS bucket_s,
       count(*) AS n,
       bar(count(*), 0, max(count(*)) OVER (), 40) AS spread
FROM deltas
WHERE delta_s > 0
GROUP BY bucket_s
ORDER BY bucket_s;
