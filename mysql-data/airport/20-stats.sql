SELECT type,COUNT(*) AS cnt
FROM airport
GROUP BY type
ORDER BY 2 DESC;

SELECT a.country_code, c.name, COUNT(*) AS cnt
FROM airport a
  INNER JOIN country c USING (country_code)
GROUP BY country_code, name
ORDER BY 3 DESC 
LIMIT 10;

SELECT * FROM airport 
WHERE country_code='AU'
AND type = 'large_airport';

SELECT c.name, a.latitude, a.longitude
FROM airport a
  INNER JOIN country c USING (country_code)
WHERE c.country_code='NO'
ORDER BY 1;
