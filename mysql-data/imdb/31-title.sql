set collation_connection = 'utf8mb4_0900_ai_ci';
SET @title='Interstellar';

SELECT * 
FROM title t
WHERE t.title = @title
AND t.type = 'movie';

SELECT t.title, t.type, r.average_rating, r.num_votes
FROM title t
JOIN title_rating r USING (tconst)
WHERE t.title = @title
AND t.type = 'movie';

SELECT t.title, t.type, g.genre 
FROM title_genre g
JOIN title t USING (title_id)
WHERE t.title = @title
AND t.type = 'movie';


SELECT DISTINCT t.title, t.type, n.name AS name, cn.name AS character_name
FROM name n
JOIN title_character tc USING (name_id)
JOIN title t USING (title_id)
JOIN character_name cn USING (character_id)
WHERE t.title = @title
AND t.type = 'movie';

SELECT t.title, t.type, n.name AS director
FROM name n
JOIN title_director td ON n.nconst = td.nconst
JOIN title t ON td.title_id = t.title_id
WHERE t.title = @title
AND t.type = 'movie';

SELECT DISTINCT t.title, t.type, np.profession
FROM name_profession np
JOIN title_principal tp ON np.name_id = tp.nconst
JOIN title t ON tp.tconst = t.tconst
WHERE t.title = @title
AND t.type = 'movie';

SELECT DISTINCT 
    t2.title AS other_movie, 
    t2.start_year, 
    n.name AS actor_name
FROM title t1
JOIN title_character tc1 ON t1.title_id = tc1.title_id
JOIN name n ON tc1.name_id = n.name_id
JOIN title_character tc2 ON n.name_id = tc2.name_id
JOIN title t2 ON tc2.title_id = t2.title_id
WHERE t1.title = @title
AND t1.type = 'movie'
AND t1.start_year = t2.start_year
AND t1.title <> t2.title
AND t2.type = 'movie'
ORDER BY t2.start_year, t2.title, n.name;


SELECT 
    COUNT(*) AS total_cast, 
    SUM(CASE WHEN tp.category = 'actor' THEN 1 ELSE 0 END) AS total_actors,
    SUM(CASE WHEN tp.category = 'actress' THEN 1 ELSE 0 END) AS total_actresses
FROM 
    title t
JOIN 
    title_principal tp ON t.tconst = tp.tconst
WHERE 
    t.title = @title
    AND t.type = 'movie';

SELECT 
    t.title, 
    r.average_rating, 
    r.num_votes
FROM 
    title t
JOIN 
    title_rating r ON t.tconst = r.tconst
WHERE 
    t.title = @title
    AND t.type = 'movie';

SELECT 
    n.name, 
    COUNT(tc.title_id) AS movie_count
FROM 
    title t
JOIN 
    title_character tc ON t.title_id = tc.title_id
JOIN 
    name n ON tc.name_id = n.name_id
WHERE 
    t.title = @title
    AND t.type = 'movie'
GROUP BY 
    n.name
ORDER BY 
    movie_count DESC
LIMIT 5;

SELECT 
    g.genre
FROM 
    title t
JOIN 
    title_genre g ON t.title_id = g.title_id
WHERE 
    t.title = @title
    AND t.type = 'movie';


SELECT 
    COUNT(*) AS total_movies, 
    SUM(run_time_mins) AS total_runtime, 
    AVG(run_time_mins) AS average_runtime
FROM 
    title
WHERE 
    start_year = (SELECT start_year FROM title WHERE title = @title AND type = 'movie')
    AND type = 'movie';

SELECT 
    np.profession, 
    COUNT(*) AS total
FROM 
    title t
JOIN 
    title_principal tp ON t.tconst = tp.tconst
JOIN 
    name_profession np ON tp.nconst = np.name_id
WHERE 
    t.title = @title
    AND t.type = 'movie'
GROUP BY 
    np.profession
ORDER BY 
    total DESC;

SELECT 
    n.name, 
    t.title, 
    r.average_rating
FROM 
    title t
JOIN 
    title_director td ON t.title_id = td.title_id
JOIN 
    name n ON td.nconst = n.nconst
JOIN 
    title_rating r ON t.tconst = r.tconst
WHERE 
    t.start_year = (SELECT start_year FROM title WHERE title = @title AND type = 'movie')
    AND t.type = 'movie'
ORDER BY 
    r.average_rating DESC
LIMIT 5;


SELECT 
    t2.title, 
    t2.start_year, 
    r.average_rating
FROM 
    title t
JOIN 
    title_director td ON t.title_id = td.title_id
JOIN 
    title_director td2 ON td.nconst = td2.nconst
JOIN 
    title t2 ON td2.title_id = t2.title_id
JOIN 
    title_rating r ON t2.tconst = r.tconst
WHERE 
    t.title = @title
    AND t.type = 'movie'
    AND t2.start_year BETWEEN t.start_year - 5 AND t.start_year + 5
    AND t.tconst <> t2.tconst
    AND t2.type = 'movie'
ORDER BY 
    t2.start_year;

SELECT 
    t2.title, 
    COUNT(DISTINCT tp.nconst) AS common_actors
FROM 
    title t
JOIN 
    title_principal tp ON t.tconst = tp.tconst
JOIN 
    title_principal tp2 ON tp.nconst = tp2.nconst
JOIN 
    title t2 ON tp2.tconst = t2.tconst
WHERE 
    t.title = @title
    AND t.type = 'movie'
    AND t2.start_year = t.start_year
    AND t.tconst <> t2.tconst
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
    title_rating r ON t2.tconst = r.tconst
WHERE 
    t.title = @title 
    AND t2.title <> t.title
    AND r.average_rating > (SELECT average_rating FROM title_rating WHERE tconst = t.tconst)
ORDER BY 
    r.average_rating DESC
LIMIT 10;

