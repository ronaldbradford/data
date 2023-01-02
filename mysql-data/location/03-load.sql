\! echo "Loading data into tables"
LOAD DATA 
  LOCAL INFILE 'location.json' 
  INTO TABLE place 
  IGNORE 0 LINES
  (@name)
  SET name = IF(JSON_VALID(@name),@name,'{"error": "invalid"}');

SELECT NOW() AS now, COUNT(*) AS cnt FROM place;
SELECT * FROM place LIMIT 10;
