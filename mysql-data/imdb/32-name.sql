SET collation_connection = 'utf8mb4_0900_ai_ci';
SET @name='Bruce Willis';

-- 1. Find all details for a specific person by name
SELECT * 
FROM   name 
WHERE  name = @name;

-- 2. Get all movies a person has appeared in
SELECT t.title, t.start_year, tp.category
FROM name n
JOIN title_principal tp USING (name_id)
JOIN title t USING (title_id)
WHERE n.name = @name
AND   t.type = 'movie'
ORDER BY t.start_year DESC;

-- 3. Find all professions for a given person
SELECT np.profession, COUNT(*) as appearances
FROM name n
JOIN name_profession np USING (name_id)
WHERE n.name = @name
GROUP BY np.profession
ORDER BY 2 desc;

-- 4. List all movies where a person was a director
SELECT t.title, t.start_year
FROM name n
JOIN title_principal tp ON tp.name_id = n.name_id
JOIN title t ON tp.title_id = t.title_id
WHERE n.name = @name
AND   t.type = 'movie'
AND   tp.category = 'director'
ORDER BY t.start_year DESC;

-- 5. Get the top-rated movies a person has acted in
SELECT t.title, r.average_rating, r.num_votes
FROM name n
JOIN title_principal tp USING (name_id)
JOIN title t USING (title_id)
JOIN title_rating r USING (title_id)
WHERE n.name = @name
AND tp.category IN ('actor', 'actress')
AND   t.type = 'movie'
ORDER BY r.average_rating DESC
LIMIT 10;

-- 6. Find all characters played by a specific person
SELECT n.name, tnc.character_name, t.title AS movie, t.start_year
FROM name n
JOIN title_name_character tnc ON n.name_id = tnc.name_id
JOIN title t ON tnc.title_id = t.title_id
WHERE n.name = @name
AND   t.type = 'movie'
ORDER BY t.start_year DESC;

-- 7. List all movies where a person worked as a writer
SELECT t.title, t.start_year
FROM name n
JOIN title_principal tp ON n.name_id = tp.name_id
JOIN title t ON t.title_id = tp.title_id
WHERE n.name = @name
AND   tp.category = 'writer'
ORDER BY t.start_year DESC;

-- 8. Find movies that a person has worked on in multiple roles (e.g., actor and director)
SELECT t.title, GROUP_CONCAT(DISTINCT tp.category) AS roles
FROM name n
JOIN title_principal tp ON n.name_id = tp.name_id
JOIN title t ON tp.title_id = t.title_id
WHERE n.name = @name
AND   t.type = 'movie'
GROUP BY t.title
HAVING COUNT(DISTINCT tp.category) > 1;

-- 9. Count the number of movies a person has appeared in each decade
SELECT 
    CONCAT(FLOOR(t.start_year / 10) * 10, 's') AS decade, 
    COUNT(*) AS num_movies
FROM name n
JOIN title_principal tp ON n.name_id = tp.name_id
JOIN title t ON tp.title_id = t.title_id
WHERE n.name = @name
AND   t.type = 'movie'
GROUP BY decade
ORDER BY decade;

-- 10. Find the most common genres the person has worked in
SELECT g.genre, COUNT(*) AS appearances
FROM name n
JOIN title_principal tp ON n.name_id = tp.name_id
JOIN title_genre g ON tp.title_id = g.title_id
WHERE n.name = @name
GROUP BY g.genre
ORDER BY appearances DESC
LIMIT 5;

-- 11. Retrieve co-actors who have worked with a specific person
SELECT DISTINCT n2.name AS co_actor, COUNT(*) AS shared_movies
FROM name n
JOIN title_principal tp1 ON n.name_id = tp1.name_id
JOIN title_principal tp2 ON tp1.title_id = tp2.title_id AND tp1.name_id != tp2.name_id
JOIN title t ON t.title_id = tp1.title_id
JOIN name n2 ON tp2.name_id = n2.name_id
WHERE n.name = @name
AND   t.type = 'movie'
GROUP BY n2.name
ORDER BY shared_movies DESC
LIMIT 10;

-- 12. Find all episodes of TV shows where the person appeared
SELECT t.title, te.season, te.episode
FROM name n
JOIN title_principal tp ON n.name_id = tp.name_id
JOIN title_episode te ON tp.title_id = te.title_id
JOIN title t ON te.parent_title_id = t.title_id
WHERE n.name = @name
AND   t.type IN ('tvEpisode','tvSeries','tvSpecial')
ORDER BY te.season, te.episode;

-- 13. List movies the person is best known for (using known_for column)
SELECT t.title, t.start_year
FROM name n
JOIN name_known_for kf ON n.name_id = kf.name_id
WHERE n.name = @name;

-- 14. Find the most recent movie a person has worked on
SELECT t.title, t.start_year
FROM name n
JOIN title_principal tp ON n.name_id = tp.name_id
JOIN title t ON tp.title_id = t.title_id
WHERE n.name = @name
ORDER BY t.start_year DESC
LIMIT 1;

-- 15. Find movies where a person played a specific character
SELECT t.title, t.start_year
FROM name n
JOIN title_name_character tnc ON n.name_id = tc.name_id
JOIN title t ON tnc.title_id = t.title_id
WHERE n.name = @name
AND tnc.character_name = 'James Bond';
