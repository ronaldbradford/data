SET SESSION  collation_connection='utf8mb4_0900_ai_ci';

DROP FUNCTION IF EXISTS SPLITSTR;
CREATE FUNCTION SPLITSTR ( st VARCHAR(255), pos INT)
RETURNS VARCHAR(255) CHARSET utf8mb4
NO SQL
DETERMINISTIC
    SQL SECURITY INVOKER
RETURN REPLACE(SUBSTRING(SUBSTRING_INDEX(st, ',' , pos),
       LENGTH(SUBSTRING_INDEX(st, ',' , pos -1)) + 1),
       ',', '');


\! echo "Creating title_genre table (CTE of CSV column)"
CREATE TABLE title_genre(title_id INT UNSIGNED NOT NULL, genre VARCHAR(20) NOT NULL, INDEX(title_id)) AS
WITH cte (title_id, genre) AS (
  SELECT t.title_id, SPLITSTR(t.genres,n.i)
  FROM title t, (SELECT 1 AS i UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) n
  WHERE SPLITSTR(t.genres,n.i) IS NOT NULL
  AND SPLITSTR(t.genres,n.i) != ''
)
SELECT * FROM cte;

SELECT 'title_genre' AS tbl, FORMAT(COUNT(*),0) FROM title_genre;
