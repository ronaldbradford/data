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
