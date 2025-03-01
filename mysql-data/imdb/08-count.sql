SELECT 'name' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM name UNION
SELECT 'title' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM title UNION
SELECT 'title_episode' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM title_episode UNION
SELECT 'title_rating' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM title_rating UNION
SELECT 'title_principal' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM title_principal UNION
SELECT 'name_profession' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM name_profession UNION
SELECT 'name_known_for' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM name_known_for UNION
SELECT 'title_genre' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM title_genre UNION
SELECT 'title_name_character' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM title_name_character UNION
SELECT 'credit' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM credit UNION
SELECT 'genre' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM genre 
ORDER BY 1;
