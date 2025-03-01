SET SESSION collation_connection='utf8mb4_0900_ai_ci';
SET SQL_BIG_SELECTS=1;

DROP FUNCTION IF EXISTS SPLITSTR;
CREATE FUNCTION SPLITSTR ( st VARCHAR(16000), pos INT)
RETURNS VARCHAR(16000) CHARSET utf8mb4
NO SQL
DETERMINISTIC
    SQL SECURITY INVOKER
RETURN REPLACE(SUBSTRING(SUBSTRING_INDEX(st, ',' , pos),
       LENGTH(SUBSTRING_INDEX(st, ',' , pos -1)) + 1),
       ',', '');

DROP TEMPORARY TABLE IF EXISTS n;
CREATE TEMPORARY TABLE n(i SMALLINT UNSIGNED AUTO_INCREMENT, PRIMARY KEY(i));
INSERT INTO n(i)
WITH RECURSIVE i AS (
  SELECT 1 AS value
  UNION ALL
  SELECT value + 1 FROM i WHERE value < 10
)
SELECT NULL FROM i;

SELECT "Creating name_profession (CTE of CSV column)" AS msg;
INSERT INTO name_profession(name_id, profession)
WITH cte (nconst, profession) AS (
  SELECT t.nconst, SPLITSTR(t.professions,n.i)
  FROM name t, n
  WHERE SPLITSTR(t.professions,n.i) IS NOT NULL
  AND SPLITSTR(t.professions,n.i) != ''
)
SELECT n.name_id, cte.profession
FROM cte
INNER JOIN name n USING (nconst);

SELECT 'name_profession' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM name_profession;
ALTER TABLE name DROP COLUMN professions;

SELECT "Creating name_knonw_for (CTE of CSV column)" AS msg;
INSERT INTO name_known_for (name_id, title_id)
WITH cte (name_id, tconst) AS (
  SELECT t.name_id, SPLITSTR(t.known_for,n.i)
  FROM name t, n
  WHERE SPLITSTR(t.known_for,n.i) IS NOT NULL
  AND SPLITSTR(t.known_for,n.i) != ''
)
SELECT c.name_id, t.title_id
FROM cte c
INNER JOIN title t USING (tconst);

SELECT 'name_known_for' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM name_known_for;
ALTER TABLE name DROP COLUMN known_for;

ALTER TABLE name ENGINE=InnoDB;

SELECT "Creating title_genre table (CTE of CSV column)" AS msg;
SELECT MAX(LENGTH(genres) - LENGTH(REPLACE(genres,',','')))+1 AS max_genres FROM title;
INSERT INTO title_genre(title_id, genre)
WITH cte (title_id, genre) AS (
  SELECT t.title_id, SPLITSTR(t.genres,n.i)
  FROM title t, n
  WHERE SPLITSTR(t.genres,n.i) IS NOT NULL
  AND SPLITSTR(t.genres,n.i) != ''
)
SELECT * FROM cte;

SELECT 'title_genre' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM title_genre;
ALTER TABLE title DROP column genres;
ALTER TABLE title ENGINE=InnoDB;

SELECT "Creating title_episode from tmp..." AS msg;
INSERT INTO title_episode(parent_title_id, title_id, season, episode)
SELECT p.title_id, t.title_id, te.season, te.episode
FROM tmp_title_episode te
INNER JOIN title t USING (tconst)
INNER JOIN title p ON p.tconst = te.parent_tconst;
DROP TABLE tmp_title_episode;
SELECT 'title_episode' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM title_episode;

SELECT "Creating title_principal from tmp..." AS msg;
INSERT INTO title_principal(title_id, name_id, ordering, category, job, characters)
SELECT t.title_id, n.name_id, p.ordering, p.category, p.job, p.characters
FROM tmp_title_principal p
INNER JOIN name n USING (nconst)
INNER JOIN title t USING (tconst);
DROP TABLE tmp_title_principal;
SELECT 'title_principal' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM title_principal;

SELECT "Creating title_rating from tmp..." AS msg;
INSERT INTO title_rating(title_id, average_rating, num_votes)
SELECT t.title_id, r.average_rating, r.num_votes
FROM tmp_title_rating r
INNER JOIN title t USING (tconst);
DROP TABLE tmp_title_rating;
SELECT 'title_rating' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM title_rating;

SELECT "Creating title_name_character" AS msg;
INSERT INTO title_name_character(title_id, name_id,character_name)
SELECT distinct tp.title_id, tp.name_id, jt.character_name
FROM title_principal tp,
     JSON_TABLE(tp.characters, '$[*]' COLUMNS (character_name VARCHAR(255) PATH '$')) jt
WHERE JSON_VALID(characters) = 1;

SELECT 'title_name_character' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM title_name_character;

SELECT 'invalid title_name_character' AS tbl, FORMAT(COUNT(*),0) AS row_count
FROM title_principal
WHERE JSON_VALID(characters) = 0;

SELECT "Creating credit summary table" AS msg;
INSERT INTO credit(name, cnt)
SELECT category, COUNT(*)
FROM title_principal
GROUP BY category
ORDER BY 2 DESC;
SELECT 'credit' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM credit;

SELECT "Creating genre summary table" AS msg;
INSERT INTO genre(genre, cnt)
SELECT genre, COUNT(*)
FROM title_genre
GROUP BY genre
ORDER BY 2 DESC;
SELECT 'genre' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM genre;
