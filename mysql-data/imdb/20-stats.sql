SELECT "Title with Star Wars in the name" AS msg;
SELECT type, COUNT(*) AS cnt
FROM title
WHERE title LIKE 'Star wars%'
GROUP BY type
ORDER BY 2 DESC;

SELECT "Star Wars Movies" AS msg;
SELECT *
FROM title
WHERE title LIKE 'Star Wars%'
AND type = 'movie'
ORDER BY start_year;

SELECT "Perfect Movies (10.0 rating)" AS msg;
SELECT t.title, tr.average_rating, tr.num_votes
FROM   title t
 INNER JOIN title_rating tr USING (title_id)
WHERE t.type='Movie'
AND   tr.average_rating=10.0
AND   tr.num_votes > 50
ORDER BY 1;


SELECT "Most voted on movies" AS msg;
SELECT t.title, tr.average_rating, tr.num_votes
FROM   title t
 INNER JOIN title_rating tr USING (title_id)
WHERE t.type='Movie'
ORDER BY 3 DESC
LIMIT 10;


SELECT "The top 10 highest-rated movies with more than 50,000 votes" AS msg;
SELECT t.title, tr.num_votes, tr.average_rating
FROM title t
JOIN title_rating tr USING (title_id)
WHERE t.type='Movie'
AND   tr.num_votes > 50000
ORDER BY tr.average_rating DESC
LIMIT 10;

SELECT "Rating Distribution" AS msg;
SELECT FLOOR(average_rating) AS rating_range, COUNT(*) AS num_titles
FROM title_rating
GROUP BY rating_range
ORDER BY rating_range;


SELECT "Release Year Trend Analysis for Movies" AS msg;
SELECT t.start_year, COUNT(*) AS movie_count, AVG(tr.average_rating) AS avg_rating
FROM title t
JOIN title_rating tr USING (title_id)
WHERE t.type='Movie'
GROUP BY t.start_year
ORDER BY t.start_year;

SELECT "Genre Influence on Ratings" AS msg;
SELECT tg.genre, AVG(tr.average_rating) AS avg_rating
FROM title_genre tg
JOIN title t USING (title_id)
JOIN title_rating tr  USING (title_id)
GROUP BY tg.genre
ORDER BY avg_rating DESC;

SELECT "Average Ratings by Decade" AS msg;
SELECT FLOOR(t.start_year / 10) * 10 AS decade, AVG(tr.average_rating) AS avg_rating, COUNT(*) as num_ratings
FROM title t
JOIN title_rating tr USING (title_id)
GROUP BY decade
ORDER BY decade;

SELECT "Top Rated TV Series" AS msg;
SELECT t.title, tr.average_rating, num_votes
FROM   title t
JOIN   title_rating tr USING (title_id)
WHERE  t.type = 'tvSeries'
AND    tr.num_votes > 10000
ORDER BY tr.average_rating DESC
LIMIT 10;

SELECT  "Longest Running TV Shows" AS msg;
SELECT t.title, (t.end_year - t.start_year) AS years_running
FROM   title t
WHERE  t.type = 'tvSeries'
AND    t.end_year IS NOT NULL
ORDER BY years_running DESC
LIMIT 10;

SELECT *
FROM   name
WHERE  name = 'Bruce Willis';

SELECT "Bruce Willis Movies" AS msg;
SELECT  t.title,t.start_year
FROM    title t
INNER JOIN title_principal tp USING (title_id)
WHERE   t.type='movie'
AND     tp.name_id = 246
ORDER BY 2;

SELECT *
FROM   name
WHERE  name = 'Christopher Nolan';

SELECT "Christopher Nolan Movies" AS msg;
SELECT DISTINCT t.title, t.start_year
FROM   title t
INNER JOIN title_principal tp USING (title_id)
WHERE  tp.name_id = 597769
AND    t.type='movie'
ORDER BY 2;

SELECT "Listed Professions" AS msg;
SELECT profession, COUNT(*)
FROM name_profession
GROUP BY profession
ORDER BY 2 DESC;

SELECT "Types of Titles" AS msg;
SELECT type, COUNT(*)
FROM title
GROUP BY type
ORDER BY 2 DESC;

SELECT "Top 100 with most titles";
SELECT n.name, COUNT(tp.title_id) AS total_movies 
FROM name n JOIN title_principal tp USING (name_id)
WHERE tp.category IN ('actor', 'actress')
GROUP BY n.name
ORDER BY total_movies DESC LIMIT 100;
