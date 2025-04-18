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

SELECT   table_schema,
         SUM(data_length+index_length)/1024/1024 AS total_mb,
         SUM(data_length)/1024/1024 AS data_mb,
         SUM(index_length)/1024/1024 AS index_mb,
         COUNT(*) AS tables,
         CURDATE() AS today
FROM     information_schema.tables
WHERE    table_schema = DATABASE()
GROUP BY table_schema
ORDER BY 2 DESC;

SELECT   IF(length(table_name)>40,CONCAT(LEFT(table_name,38),'..'),table_name) AS table_name,
         engine,row_format AS format, table_rows, avg_row_length AS avg_row,
         round((data_length+index_length)/1024/1024,2) AS total_mb,
         round((data_length)/1024/1024,2) AS data_mb,
         round((index_length)/1024/1024,2) AS index_mb
FROM     information_schema.tables
WHERE    table_schema=DATABASE()
AND      table_type='BASE TABLE'
ORDER BY 6 DESC;
