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

SELECT "Creating title_genre table (CTE of CSV column)" AS msg;
CREATE TABLE title_genre(title_id INT UNSIGNED NOT NULL, genre VARCHAR(20) NOT NULL, INDEX(title_id)) AS
WITH cte (title_id, genre) AS (
  SELECT t.title_id, SPLITSTR(t.genres,n.i)
  FROM title t, (SELECT 1 AS i UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) n
  WHERE SPLITSTR(t.genres,n.i) IS NOT NULL
  AND SPLITSTR(t.genres,n.i) != ''
)
SELECT * FROM cte;
ALTER TABLE title DROP column genres;
SELECT 'title_genre' AS tbl, FORMAT(COUNT(*),0) FROM title_genre;

SELECT "Creating name_profession (CTE of CSV column)" AS msg;
CREATE TABLE name_profession(name_id INT UNSIGNED NOT NULL, profession VARCHAR(30) NOT NULL, INDEX(name_id)) AS
WITH cte (name_id, profession) AS (
  SELECT t.name_id, SPLITSTR(t.professions,n.i)
  FROM name t, (SELECT 1 AS i UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) n
  WHERE SPLITSTR(t.professions,n.i) IS NOT NULL
  AND SPLITSTR(t.professions,n.i) != ''
)
SELECT * FROM cte;
ALTER TABLE name DROP COLUMN professions;
SELECT 'name_profession' AS tbl, FORMAT(COUNT(*),0) FROM name_profession;


SELECT MAX(LENGTH(directors) - LENGTH(REPLACE(directors,',','')))+1 AS parts FROM title_crew;

SELECT "Creating title_director (CTE of CSV column)" AS msg;
CREATE TABLE title_director(title_id INT UNSIGNED NOT NULL, nconst CHAR(10) NOT NULL, INDEX(title_id), INDEX(nconst)) AS
WITH cte (title_id, directors) AS (
  SELECT t.title_id, SPLITSTR(tc.directors,n.i)
  FROM n,
       title_crew tc
  INNER JOIN title t USING (tconst)
  WHERE SPLITSTR(tc.directors,n.i) IS NOT NULL
  AND   SPLITSTR(tc.directors,n.i) != ''
)
SELECT * FROM cte;
/* 7,781,533 n=4,  7,870,520 n=10 10m, 7,906,588 n=10 25m*/

ALTER TABLE title_crew DROP COLUMN directors;

CREATE TABLE title_writer(title_id INT UNSIGNED NOT NULL, nconst CHAR(10) NOT NULL, INDEX(title_id), INDEX(nconst)) AS
WITH cte (title_id, nconst) AS (
  SELECT t.title_id, SPLITSTR(tc.writers,n.i)
  FROM n,
       title_crew tc
  INNER JOIN title t USING (tconst)
  WHERE SPLITSTR(tc.writers,n.i) IS NOT NULL
  AND   SPLITSTR(tc.writers,n.i) != ''
)
SELECT * FROM cte;
/* 7,781,533 n=4,  7,870,520 n=10 10m, 7,906,588 n=10 25m*/

ALTER TABLE title_crew DROP COLUMN writers;

SELECT 'title_director (<=10)' AS tbl, FORMAT(COUNT(*),0) FROM title_director;

/* TODO: Create subset > 10, numbers and reapply.
DELETE FROM n;
INSERT INTO n(i)
WITH RECURSIVE i AS (
  SELECT 1 AS value
  UNION ALL
  SELECT value + 1 FROM i WHERE value < 10
)
SELECT NULL FROM i;

CREATE TABLE tmp_title_directors
SELECT  tc.tconst, tc.directors
FROM    title_crew tc
WHERE   (LENGTH(tc.directors) - LENGTH(REPLACE(tc.directors,',','')))+1 > 10;
