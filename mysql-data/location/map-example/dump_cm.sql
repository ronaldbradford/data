SET @cc = 'cm';   -- lowercase, matches place.country_code

  SELECT JSON_OBJECT(
    'type', 'FeatureCollection',
    'features', JSON_ARRAYAGG(
      JSON_OBJECT(
        'type', 'Feature',
        'geometry', JSON_OBJECT(
          'type', 'Point',
          'coordinates', JSON_ARRAY(
            CAST(name->>'$.lon' AS DECIMAL(10,7)),
            CAST(name->>'$.lat' AS DECIMAL(10,7))
          )
        ),
        'properties', JSON_OBJECT(
          'place_id',     place_id,
          'display_name', display_name,
          'city',         name->>'$.address.city',
          'country_code', UPPER(country_code)
        )
      )
    )
  ) AS geojson
  FROM place
  WHERE country_code = @cc
    AND name->>'$.lat' IS NOT NULL
    AND name->>'$.lon' IS NOT NULL;
