set collation_connection = 'utf8mb4_0900_ai_ci';
SET @name='Bruce Willis';


-- 1. Find all details for a specific person by name
SELECT * 
FROM name 
WHERE name = @name;

-- 2. Get all movies a person has appeared in
SELECT t.title, t.start_year, tp.category
FROM name n
JOIN title_principal tp ON n.nconst = tp.nconst
JOIN title t ON tp.tconst = t.tconst
WHERE n.name = @name
AND   t.type = 'movie'
ORDER BY t.start_year DESC;

-- 3. Find all professions for a given person
SELECT np.profession
FROM name n
JOIN name_profession np ON n.name_id = np.name_id
WHERE n.name = @name;

SELECT np.profession, COUNT(*) as appearances
FROM name n
JOIN name_profession np ON n.name_id = np.name_id
WHERE n.name = @name
GROUP BY np.profession
ORDER BY 2 desc;

-- 4. List all movies where a person was a director
SELECT t.title, t.start_year
FROM name n
JOIN title_director td ON n.nconst = td.nconst
JOIN title t ON td.title_id = t.title_id
WHERE n.name = @name
AND   t.type = 'movie'
ORDER BY t.start_year DESC;

-- 5. Get the top-rated movies a person has acted in
SELECT t.title, r.average_rating, r.num_votes
FROM name n
JOIN title_principal tp ON n.nconst = tp.nconst
JOIN title t ON tp.tconst = t.tconst
JOIN title_rating r ON t.tconst = r.tconst
WHERE n.name = @name AND tp.category IN ('actor', 'actress')
AND   t.type = 'movie'
ORDER BY r.average_rating DESC
LIMIT 10;

-- 6. Find all characters played by a specific person
SELECT n.name, cn.name AS character_name, t.title AS movie, t.start_year
FROM name n
JOIN title_character tc ON n.name_id = tc.name_id
JOIN character_name cn ON tc.character_id = cn.character_id
JOIN title t ON tc.title_id = t.title_id
WHERE n.name = @name
AND   t.type = 'movie'
ORDER BY t.start_year DESC;

-- 7. List all movies where a person worked as a writer
SELECT t.title, t.start_year
FROM name n
JOIN title_crew tc ON tc.writers LIKE CONCAT('%', n.nconst, '%')
JOIN title t ON tc.tconst = t.tconst
WHERE n.name = @name
ORDER BY t.start_year DESC;

-- 8. Find movies that a person has worked on in multiple roles (e.g., actor and director)
SELECT t.title, GROUP_CONCAT(DISTINCT tp.category) AS roles
FROM name n
JOIN title_principal tp ON n.nconst = tp.nconst
JOIN title t ON tp.tconst = t.tconst
WHERE n.name = @name
AND   t.type = 'movie'
GROUP BY t.title
HAVING COUNT(DISTINCT tp.category) > 1;

-- 9. Count the number of movies a person has appeared in each decade
SELECT 
    CONCAT(FLOOR(t.start_year / 10) * 10, 's') AS decade, 
    COUNT(*) AS num_movies
FROM name n
JOIN title_principal tp ON n.nconst = tp.nconst
JOIN title t ON tp.tconst = t.tconst
WHERE n.name = @name
AND   t.type = 'movie'
GROUP BY decade
ORDER BY decade;

-- 10. Find the most common genres the person has worked in
SELECT g.genre, COUNT(*) AS appearances
FROM name n
JOIN title_principal tp ON n.nconst = tp.nconst
JOIN title_genre g ON tp.tconst = g.title_id
WHERE n.name = @name
GROUP BY g.genre
ORDER BY appearances DESC
LIMIT 5;

-- 11. Retrieve co-actors who have worked with a specific person
SELECT DISTINCT n2.name AS co_actor, COUNT(*) AS shared_movies
FROM name n
JOIN title_principal tp1 ON n.nconst = tp1.nconst
JOIN title_principal tp2 ON tp1.tconst = tp2.tconst AND tp1.nconst != tp2.nconst
JOIN title t ON t.tconst = tp1.tconst
JOIN name n2 ON tp2.nconst = n2.nconst
WHERE n.name = @name
AND   t.type = 'movie'
GROUP BY n2.name
ORDER BY shared_movies DESC
LIMIT 10;

-- 12. Find all episodes of TV shows where the person appeared
SELECT t.title, te.season, te.episode
FROM name n
JOIN title_principal tp ON n.nconst = tp.nconst
JOIN title_episode te ON tp.tconst = te.tconst
JOIN title t ON te.parent_tconst = t.tconst
WHERE n.name = @name
AND   t.type IN ('tvEpisode','tvSeries','tvSpecial')
ORDER BY te.season, te.episode;

-- 13. List movies the person is best known for (using known_for column)
SELECT t.title, t.start_year
FROM name n
JOIN title t ON FIND_IN_SET(t.tconst, n.known_for) > 0
WHERE n.name = @name;

-- 14. Find the most recent movie a person has worked on
SELECT t.title, t.start_year
FROM name n
JOIN title_principal tp ON n.nconst = tp.nconst
JOIN title t ON tp.tconst = t.tconst
WHERE n.name = @name
ORDER BY t.start_year DESC
LIMIT 1;

-- 15. Find movies where a person played a specific character
SELECT t.title, t.start_year
FROM name n
JOIN title_character tc ON n.name_id = tc.name_id
JOIN character_name cn ON tc.character_id = cn.character_id
JOIN title t ON tc.title_id = t.title_id
WHERE n.name = @name AND cn.name = 'James Bond';


