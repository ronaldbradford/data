SELECT genre,COUNT(*) AS titles 
FROM title_genre 
GROUP BY genre 
ORDER BY 2 DESC
LIMIT 20;
