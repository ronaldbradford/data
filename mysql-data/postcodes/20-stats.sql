SELECT COUNT(DISTINCT country_code) AS country_count FROM postcode;
SELECT COUNT(*) AS australia_count FROM postcode WHERE country_code='AU';
SELECT COUNT(*) AS us_count FROM postcode WHERE country_code='US';

SELECT * FROM postcode WHERE country_code='AU' AND postal_code='4370';
SELECT * FROM postcode WHERE country_code='US' AND postal_code='90210';

SELECT COUNT(DISTINCT country_code) AS country_count FROM postcode_geo;

SELECT *, ST_AsGeoJSON(location) FROM postcode_geo WHERE country_code='AU' AND postal_code='4370';

/* This sets variable to NULL and does not work */
SELECT @warwick = g.location
FROM  postcode_geo g 
INNER JOIN postcode p USING (postcode_id)
WHERE p.country_code = 'AU'
AND   p.postal_code = '4370'
AND   p.place_name = 'Warwick'
LIMIT 1;

SELECT p.place_name, ST_Distance_Sphere(w.location, g.location)
FROM  postcode_geo g 
INNER JOIN postcode p USING (postcode_id)
JOIN (
      SELECT g.location
      FROM  postcode_geo g
      INNER JOIN postcode p USING (postcode_id)
      WHERE p.country_code = 'AU'
      AND   p.postal_code = '4370'
      AND   p.place_name = 'Warwick'
      LIMIT 1 
     ) w
WHERE p.country_code = 'AU'
AND   p.postal_code = '4370'
ORDER BY p.place_name;

SELECT ST_Distance_Sphere(@warwick, location)
FROM  postcode_geo
