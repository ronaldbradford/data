SELECT COUNT(DISTINCT country_code) AS country_count FROM postcode;
SELECT COUNT(*) AS australia_count FROM postcode WHERE country_code='AU';
SELECT COUNT(*) AS us_count FROM postcode WHERE country_code='US';

SELECT * FROM postcode WHERE country_code='AU' AND postal_code='4370';
SELECT * FROM postcode WHERE country_code='US' AND postal_code='90210';

SELECT country_code, COUNT(*) AS country_count
FROM postcode
GROUP BY country_code
ORDER BY 2 DESC
LIMIT 10;

SELECT COUNT(DISTINCT country_code) AS country_count FROM postcode_geo;
