SELECT type,COUNT(*) AS cnt
FROM airport
GROUP BY type
ORDER BY 2 DESC;

SELECT * FROM airport 
WHERE country_code='AU'
AND type = 'large_airport';
