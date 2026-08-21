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
