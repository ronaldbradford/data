set collation_connection = 'utf8mb4_0900_ai_ci';
SET @title='Interstellar';

SELECT * 
FROM title t
WHERE t.title = @title
AND t.type = 'movie';

SELECT t.title, t.type, r.average_rating, r.num_votes
FROM title t
JOIN title_rating r USING (title_id)
WHERE t.title = @title
AND t.type = 'movie';

SELECT t.title, t.type, g.genre 
FROM title_genre g
JOIN title t USING (title_id)
WHERE t.title = @title
AND t.type = 'movie';

SELECT DISTINCT t.title, t.type, n.name AS name, tnc.character_name
FROM name n
JOIN title_name_character tnc USING (name_id)
JOIN title t USING (title_id)
WHERE t.title = @title
AND t.type = 'movie';

SELECT t.title, t.type, n.name AS director
FROM name n
JOIN title_principal tp USING (name_id)
JOIN title t USING (title_id)
WHERE t.title = @title
AND   tp.category = 'director'
AND t.type = 'movie';

SELECT DISTINCT t.title, t.type, np.profession
FROM name_profession np
JOIN title_principal tp ON np.name_id = tp.name_id
JOIN title t ON tp.title_id = t.title_id
WHERE t.title = @title
AND t.type = 'movie';

SELECT 
    COUNT(*) AS total_cast, 
    SUM(CASE WHEN tp.category = 'actor' THEN 1 ELSE 0 END) AS total_actors,
    SUM(CASE WHEN tp.category = 'actress' THEN 1 ELSE 0 END) AS total_actresses
FROM 
    title t
JOIN 
    title_principal tp USING (title_id)
WHERE 
    t.title = @title
    AND t.type = 'movie';

SELECT 'Movies in the same year' AS msg, 
    start_year AS release_year,
    COUNT(*) AS total_movies, 
    SUM(run_time_mins) AS total_runtime, 
    AVG(run_time_mins) AS average_runtime
FROM 
    title
WHERE 
    start_year = (SELECT start_year FROM title WHERE title = @title AND type = 'movie')
    AND type = 'movie';

SELECT 
    n.name, 
    t.title, 
    r.average_rating
FROM 
    title t
JOIN 
    title_principal tp USING (title_id)
JOIN 
    name n USING (name_id)
JOIN 
    title_rating r USING (title_id)
WHERE 
    t.start_year = (SELECT start_year FROM title WHERE title = @title AND type = 'movie')
    AND t.type = 'movie'
    AND tp.category = 'director'
ORDER BY 
    r.average_rating DESC
LIMIT 5;

SELECT 
    t2.title, 
    COUNT(DISTINCT tp.name_id) AS common_actors
FROM 
    title t
JOIN 
    title_principal tp ON t.title_id = tp.title_id
JOIN 
    title_principal tp2 ON tp.name_id = tp2.name_id
JOIN 
    title t2 ON tp2.title_id = t2.title_id
WHERE 
    t.title = @title
    AND t.type = 'movie'
    AND t2.start_year = t.start_year
    AND t.title_id <> t2.title_id
    AND t2.type = 'move'
GROUP BY 
    t2.title
ORDER BY 
    common_actors DESC;

SELECT 
    t2.title, 
    r.average_rating, 
    r.num_votes
FROM 
    title t
JOIN 
    title_genre g1 ON t.title_id = g1.title_id
JOIN 
    title_genre g2 ON g1.genre = g2.genre
JOIN 
    title t2 ON g2.title_id = t2.title_id
JOIN 
    title_rating r ON t2.title_id = r.title_id
WHERE 
    t.title = @title 
    AND t2.title <> t.title
    AND r.average_rating > (SELECT average_rating FROM title_rating WHERE title_id = t.title_id)
ORDER BY 
    r.average_rating DESC
LIMIT 10;
