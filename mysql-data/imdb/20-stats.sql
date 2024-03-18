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
SELECT t.title, tr.average_rating, tr.num_votes
FROM   title t
 INNER JOIN title_rating tr USING (tconst)
WHERE t.type='Movie'
AND   tr.average_rating=10.0
AND   tr.num_votes > 50
ORDER BY 1;


\! echo "Most voted on movies"
SELECT t.title, tr.average_rating, tr.num_votes
FROM   title t
 INNER JOIN title_rating tr USING (tconst)
WHERE t.type='Movie'
ORDER BY 3 DESC
LIMIT 10;


\! echo "Top Rated Movies Query: Find the top 10 highest-rated movies with more than 10,000 votes."
SELECT t.title, tr.average_rating
FROM title t
JOIN title_rating tr ON t.tconst = tr.tconst
WHERE tr.num_votes > 10000
ORDER BY tr.average_rating DESC
LIMIT 10;

\! echo "Rating Distribution"
SELECT FLOOR(average_rating) AS rating_range, COUNT(*) AS num_movies
FROM title_rating
GROUP BY rating_range
ORDER BY rating_range;


\! echo "Release Year Trend Analysis"
SELECT t.start_year, AVG(tr.average_rating) AS avg_rating
FROM title t
JOIN title_rating tr ON t.tconst = tr.tconst
GROUP BY t.start_year
ORDER BY t.start_year;

\! echo "Genre Influence on Ratings"
SELECT tg.genre, AVG(tr.average_rating) AS avg_rating
FROM title_genre tg
JOIN title t ON tg.title_id = t.title_id
JOIN title_rating tr ON t.tconst = tr.tconst
GROUP BY tg.genre
ORDER BY avg_rating DESC;

\! echo "Average Ratings by Decade"
SELECT FLOOR(t.start_year / 10) * 10 AS decade, AVG(tr.average_rating) AS avg_rating, COUNT(*) as num_ratings
FROM title t
JOIN title_rating tr ON t.tconst = tr.tconst
GROUP BY decade
ORDER BY decade;

\! echo "Top Rated TV Series"
SELECT t.title, tr.average_rating, num_votes
FROM title t
JOIN title_rating tr ON t.tconst = tr.tconst
WHERE t.type = 'tvSeries' AND tr.num_votes > 5000
ORDER BY tr.average_rating DESC
LIMIT 10;

\! echo "Longest Running TV Shows"
SELECT t.title, (t.end_year - t.start_year) AS years_running
FROM title t
WHERE t.type = 'tvSeries' AND t.end_year IS NOT NULL
ORDER BY years_running DESC
LIMIT 10;

\! echo "Bruce Willis Movies"
SELECT t.title,t.start_year
FROM title t
INNER JOIN title_principal tp USING (tconst)
WHERE t.type='movie'
AND tp.ordering=1
AND tp. category='actor'
AND tp.nconst='nm0000246'
ORDER BY 2;

\! echo "Christopher Nolan Movies"
SELECT t.title, t.start_year
FROM title t
INNER JOIN title_principal tp USING (tconst)
WHERE tp.nconst = 'nm0634240'
AND t.type='movie'
ORDER BY 2;
