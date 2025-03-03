SELECT "Loading names for IMDb" AS msg;
LOAD DATA 
  LOCAL INFILE 'name.basics.tsv' 
  INTO TABLE name 
  FIELDS TERMINATED BY '\t' 
  IGNORE 1 LINES
  (nconst, @name, born, died, @professions, @known_for)
  SET name        = IF(name = '', 'Unknown', @name),
      professions = IF(professions = '', NULL, @professions),
      known_for   = IF(known_for = '',   NULL, @known_for);

SHOW WARNINGS;

SELECT 'name' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM name;

SELECT "Loading titles for IMDb" AS msg;
LOAD DATA 
  LOCAL INFILE 'title.basics.tsv' 
  INTO TABLE title 
  FIELDS TERMINATED BY '\t' 
  IGNORE 1 LINES
  (tconst, type, title, original_title, is_adult, start_year, end_year, run_time_mins, genres);

SHOW WARNINGS;
  
SELECT 'title' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM title;

SELECT "Removing 'adult' titles" AS msg;
SELECT is_adult, COUNT(*) AS row_count FROM title GROUP BY is_adult;
DELETE FROM title WHERE is_adult=1;

SELECT "Loading title episodes for IMDb" AS msg;
LOAD DATA 
  LOCAL INFILE 'title.episode.tsv' 
  INTO TABLE tmp_title_episode
  FIELDS TERMINATED BY '\t' 
  IGNORE 1 LINES;

SHOW WARNINGS;

SELECT 'title_episode' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM title_episode;

SELECT "Loading title ratings for IMDb" AS msg;
LOAD DATA
  LOCAL INFILE 'title.ratings.tsv'
  INTO TABLE tmp_title_rating
  FIELDS TERMINATED BY '\t'
  IGNORE 1 LINES
  (tconst, average_rating, num_votes);

SHOW WARNINGS;

SELECT 'tmp_title_rating' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM tmp_title_rating;

SELECT "Loading title principals for IMDb" AS msg;
LOAD DATA 
  LOCAL INFILE 'title.principals.tsv' 
  INTO TABLE tmp_title_principal
  FIELDS TERMINATED BY '\t' 
  IGNORE 1 LINES;

SHOW WARNINGS;

SELECT 'tmp_title_principal' AS tbl, FORMAT(COUNT(*),0) AS row_count FROM tmp_title_principal;
