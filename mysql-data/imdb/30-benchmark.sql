-- 1. Lookup a movie by title
SELECT * 
FROM title 
WHERE title = 'Inception';

-- 2. Find all movies released in a specific year
SELECT title, start_year 
FROM title 
WHERE start_year = 2020;

-- 3. Get the rating of a specific movie
SELECT t.title, r.average_rating, r.num_votes 
FROM title t
JOIN title_rating r ON t.tconst = r.tconst
WHERE t.title = 'The Godfather';

-- 4. Retrieve all movies of a given genre
SELECT t.title 
FROM title t
JOIN title_genre g ON t.title_id = g.title_id
WHERE g.genre = 'Drama';

-- 5. Find all actors in a specific movie
SELECT DISTINCT n.name
FROM name n
JOIN title_character tc ON n.name_id = tc.name_id
JOIN title t ON tc.title_id = t.title_id
WHERE t.title = 'The Dark Knight';

SELECT DISTINCT n.name, cn.name
FROM name n
JOIN title_character tc USING (name_id)
JOIN title t USING (title_id)
JOIN character_name cn USING (character_id)
WHERE t.title = 'The Dark Knight';

-- 6. Get all movies directed by a specific person
SELECT t.title 
FROM title t
JOIN title_director td ON t.title_id = td.title_id
WHERE td.nconst = 'nm000001';

-- 7. Lookup a person by their name
SELECT * 
FROM name 
WHERE name = 'Christopher Nolan';

-- 8. Find the most recent movies
SELECT title, start_year 
FROM title 
ORDER BY start_year DESC 
LIMIT 10;

-- 9. Get all genres associated with a specific movie
SELECT g.genre 
FROM title_genre g
JOIN title t ON g.title_id = t.title_id
WHERE t.title = 'Interstellar';

-- 10. Retrieve all movies with a specific minimum rating
SELECT t.title, r.average_rating 
FROM title t
JOIN title_rating r ON t.tconst = r.tconst
WHERE r.average_rating >= 8.0
ORDER BY r.average_rating DESC;

-- 11. Get the count of movies per genre
SELECT genre, COUNT(*) AS movie_count 
FROM title_genre 
GROUP BY genre;

-- 12. Find the character names played in a specific movie
SELECT cn.name 
FROM character_name cn
JOIN title_character tc ON cn.character_id = tc.character_id
JOIN title t ON tc.title_id = t.title_id
WHERE t.title = 'Avengers: Endgame';

-- 13. Find all directors of a specific movie
SELECT n.name 
FROM name n
JOIN title_director td ON n.nconst = td.nconst
JOIN title t ON td.title_id = t.title_id
WHERE t.title = 'Pulp Fiction';

-- 14. Get the total number of movies per year
SELECT start_year, COUNT(*) AS total_movies 
FROM title 
GROUP BY start_year 
ORDER BY start_year DESC;

-- 15. Lookup an episode of a TV show by season and episode number
SELECT t.title 
FROM title_episode e
JOIN title t ON e.tconst = t.tconst
WHERE e.parent_tconst = 'tt0903747' -- Breaking Bad
  AND e.season = 5 
  AND e.episode = 14;

-- 16. Find all titles in which a given person has appeared
SELECT t.title 
FROM title t
JOIN title_principal tp ON t.tconst = tp.tconst
WHERE tp.nconst = 'nm0000138';

-- 17. Count the number of titles per content type (e.g., movie, tvSeries)
SELECT type, COUNT(*) AS count 
FROM title 
GROUP BY type;

-- 18. Find the highest-rated movie
SELECT t.title, r.average_rating 
FROM title t
JOIN title_rating r ON t.tconst = r.tconst
ORDER BY r.average_rating DESC 
LIMIT 1;

-- 19. Get all jobs associated with a given person in movies
SELECT tp.job, t.title 
FROM title_principal tp
JOIN title t ON tp.tconst = t.tconst
WHERE tp.nconst = 'nm0000199';

-- 20. Find all movies with a runtime greater than 150 minutes
SELECT title, run_time_mins 
FROM title 
WHERE run_time_mins > 150;


SELECT 
    t.title, 
    t.start_year, 
    r.average_rating, 
    r.num_votes
FROM 
    title t
JOIN 
    title_rating r ON t.tconst = r.tconst
WHERE 
    t.type = 'movie'  -- Ensure we're selecting movies only
ORDER BY 
    r.num_votes DESC,  -- Sort by number of votes (popularity)
    r.average_rating DESC  -- Further sort by rating in case of ties
LIMIT 1000;


SELECT t.tconst, t.title, t.original_title, t.start_year, t.run_time_mins, t.genres, r.average_rating, r.num_votes
FROM title t
LEFT JOIN title_rating r ON t.tconst = r.tconst
WHERE t.title = 'The Matrix';

SELECT t.title, t.start_year, r.average_rating, r.num_votes
FROM title t
JOIN title_rating r ON t.tconst = r.tconst
JOIN title_genre g ON t.title_id = g.title_id
WHERE g.genre = 'Action'
ORDER BY r.average_rating DESC, r.num_votes DESC
LIMIT 10;

SELECT t.title, t.start_year, n.name
FROM title t
JOIN title_character tc ON t.title_id = tc.title_id
JOIN name n ON tc.name_id = n.name_id
WHERE n.name = 'Tom Hanks';

SELECT n.name, COUNT(td.title_id) AS num_titles
FROM title_director td
JOIN name n ON td.nconst = n.nconst
GROUP BY n.name
ORDER BY num_titles DESC
LIMIT 10;

SELECT FLOOR(t.start_year / 10) * 10 AS decade, AVG(r.average_rating) AS avg_rating
FROM title t
JOIN title_rating r ON t.tconst = r.tconst
WHERE t.start_year IS NOT NULL
GROUP BY decade
ORDER BY decade;

SELECT t.title, n.name
FROM title t
JOIN title_director td ON t.title_id = td.title_id
JOIN title_principal tp ON t.tconst = tp.tconst AND tp.category = 'actor'
JOIN name n ON td.nconst = tp.nconst
WHERE n.name = 'Clint Eastwood';

SELECT t.title, r.num_votes
FROM title t
JOIN title_rating r ON t.tconst = r.tconst
ORDER BY r.num_votes DESC
LIMIT 10;

SELECT n.name, COUNT(DISTINCT g.genre) AS genre_count
FROM title_character tc
JOIN name n ON tc.name_id = n.name_id
JOIN title_genre g ON tc.title_id = g.title_id
GROUP BY n.name
HAVING genre_count > 1
ORDER BY genre_count DESC
LIMIT 10;

SELECT t.title, t.start_year, t.end_year, (t.end_year - t.start_year) AS duration
FROM title t
WHERE t.type = 'tvSeries'
ORDER BY duration DESC
LIMIT 10;

SELECT t.title, COUNT(td.nconst) AS director_count
FROM title t
JOIN title_director td ON t.title_id = td.title_id
GROUP BY t.title
ORDER BY director_count DESC
LIMIT 10;

SELECT cn.name AS character_name, n.name AS actor_name, COUNT(*) AS appearances
FROM title_character tc
JOIN character_name cn ON tc.character_id = cn.character_id
JOIN name n ON tc.name_id = n.name_id
GROUP BY cn.name, n.name
HAVING appearances > 1
ORDER BY appearances DESC;

SELECT genre, COUNT(*) AS genre_count
FROM title_genre
GROUP BY genre
ORDER BY genre_count DESC
LIMIT 10;

SELECT DISTINCT n1.name AS actor_1, n2.name AS actor_2, t.title
FROM title_character tc1
JOIN title_character tc2 ON tc1.title_id = tc2.title_id AND tc1.name_id != tc2.name_id
JOIN name n1 ON tc1.name_id = n1.name_id
JOIN name n2 ON tc2.name_id = n2.name_id
JOIN title t ON tc1.title_id = t.title_id
WHERE n1.name = 'Leonardo DiCaprio';

SELECT profession, COUNT(*) AS count
FROM name_profession
GROUP BY profession
ORDER BY count DESC;

SELECT e.tconst, t.title, e.season, e.episode
FROM title_episode e
JOIN title t ON e.tconst = t.tconst
WHERE e.parent_tconst = 'tt0944947'  -- Game of Thrones
ORDER BY e.season, e.episode;


-- 1. Find the average movie runtime per genre
SELECT 
    g.genre, 
    AVG(t.run_time_mins) AS avg_runtime
FROM 
    title t
JOIN 
    title_genre g ON t.title_id = g.title_id
WHERE 
    t.run_time_mins IS NOT NULL
GROUP BY 
    g.genre
ORDER BY 
    avg_runtime DESC;

-- 2. Find the top 5 most prolific actors (by number of titles)
SELECT 
    n.name, 
    COUNT(tc.title_id) AS num_movies
FROM 
    title_character tc
JOIN 
    name n ON tc.name_id = n.name_id
GROUP BY 
    n.name
ORDER BY 
    num_movies DESC
LIMIT 5;

-- 3. Calculate the distribution of movies per year
SELECT 
    start_year, 
    COUNT(*) AS movie_count
FROM 
    title
WHERE 
    start_year IS NOT NULL
GROUP BY 
    start_year
ORDER BY 
    start_year;

-- 4. Determine the highest-rated movie per genre
SELECT 
    g.genre, 
    t.title, 
    r.average_rating
FROM 
    title_genre g
JOIN 
    title t ON g.title_id = t.title_id
JOIN 
    title_rating r ON t.tconst = r.tconst
WHERE 
    r.average_rating = (SELECT MAX(r2.average_rating) 
                        FROM title_rating r2 
                        JOIN title_genre g2 ON r2.tconst = g2.title_id 
                        WHERE g2.genre = g.genre)
ORDER BY 
    g.genre, r.average_rating DESC;

-- 5. Find directors with the highest average movie rating (minimum 5 movies)
SELECT 
    n.name, 
    AVG(r.average_rating) AS avg_rating, 
    COUNT(td.title_id) AS num_movies
FROM 
    title_director td
JOIN 
    title t ON td.title_id = t.title_id
JOIN 
    title_rating r ON t.tconst = r.tconst
JOIN 
    name n ON td.nconst = n.nconst
GROUP BY 
    n.name
HAVING 
    COUNT(td.title_id) >= 5
ORDER BY 
    avg_rating DESC
LIMIT 10;

-- 6. Rank movies within each genre by rating
SELECT 
    g.genre, 
    t.title, 
    r.average_rating,
    RANK() OVER (PARTITION BY g.genre ORDER BY r.average_rating DESC) AS rank_in_genre
FROM 
    title_genre g
JOIN 
    title t ON g.title_id = t.title_id
JOIN 
    title_rating r ON t.tconst = r.tconst;

-- 7. Find the number of movies released per decade
SELECT 
    CONCAT(FLOOR(start_year / 10) * 10, 's') AS decade, 
    COUNT(*) AS movie_count
FROM 
    title
WHERE 
    start_year IS NOT NULL
GROUP BY 
    decade
ORDER BY 
    decade;

-- 8. Calculate the actor who has played the most unique roles
SELECT 
    n.name, 
    COUNT(DISTINCT c.name) AS unique_characters
FROM 
    title_character tc
JOIN 
    name n ON tc.name_id = n.name_id
JOIN 
    character_name c ON tc.character_id = c.character_id
GROUP BY 
    n.name
ORDER BY 
    unique_characters DESC
LIMIT 10;

-- 9. Find the genre with the highest total number of votes
SELECT 
    g.genre, 
    SUM(r.num_votes) AS total_votes
FROM 
    title_genre g
JOIN 
    title_rating r ON g.title_id = r.tconst
GROUP BY 
    g.genre
ORDER BY 
    total_votes DESC;

