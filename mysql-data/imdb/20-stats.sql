SELECT category, COUNT(*) AS cnt
FROM title_principal
GROUP BY category
ORDER BY 2 DESC;

SELECT genre,COUNT(*) AS titles 
FROM title_genre 
GROUP BY genre 
ORDER BY 2 DESC
LIMIT 20;

\! echo "Title with Star Wars in the name"
SELECT type, COUNT(*) AS cnt
FROM title
WHERE title LIKE 'Star wars%'
GROUP BY type
ORDER BY 2 DESC;

\! echo "Star Wars Movies"
SELECT *
FROM title
WHERE title LIKE 'Star Wars%'
AND type = 'movie'
ORDER BY start_year;

\! echo "Perfect Movies (10.0 rating)"
SELECT t.title, tr.averageRating, tr.numVotes
FROM   title t
 INNER JOIN title_rating tr USING (tconst)
WHERE t.type='Movie'
AND   tr.averageRating=10.0
AND   tr.numVotes > 50
ORDER BY 1;


\! echo "Most voted on movies"
SELECT t.title, tr.averageRating, tr.numVotes
FROM   title t
 INNER JOIN title_rating tr USING (tconst)
WHERE t.type='Movie'
ORDER BY 3 DESC
LIMIT 10;
