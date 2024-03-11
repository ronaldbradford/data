\! echo "Loading names for IMDb"
LOAD DATA 
  LOCAL INFILE 'name.basics.tsv' 
  INTO TABLE name 
  FIELDS TERMINATED BY '\t' 
  IGNORE 1 LINES
  (nconst, name, born, died, @professions, known_for)
  SET professions = IF(professions = '',NULL,@professions);

SHOW WARNINGS;

SELECT 'name' AS tbl, FORMAT(COUNT(*),0) AS cnt FROM name;

\! echo "Loading titles for IMDb"
LOAD DATA 
  LOCAL INFILE 'title.basics.tsv' 
  INTO TABLE title 
  FIELDS TERMINATED BY '\t' 
  IGNORE 1 LINES
  (tconst, type, title, original_title, is_adult, start_year, end_year, run_time_mins, genres);

SHOW WARNINGS;
  
SELECT 'title' AS tbl, FORMAT(COUNT(*),0) AS cnt FROM title;

\! echo "Removing 'adult' titles"
SELECT is_adult, COUNT(*) AS cnt FROM title GROUP BY is_adult;
DELETE FROM title WHERE is_adult=1;

\! echo "Loading title episodes for IMDb"
LOAD DATA 
  LOCAL INFILE 'title.episode.tsv' 
  INTO TABLE title_episode 
  FIELDS TERMINATED BY '\t' 
  IGNORE 1 LINES;

SHOW WARNINGS;

SELECT 'title_episode' AS tbl, FORMAT(COUNT(*),0) AS cnt FROM title_episode;

\! echo "Loading title crew for IMDb"
LOAD DATA 
  LOCAL INFILE 'title.crew.tsv' 
  INTO TABLE title_crew 
  FIELDS TERMINATED BY '\t' 
  IGNORE 1 LINES
  (tconst, directors, writers);

SHOW WARNINGS;

SELECT 'title_crew' AS tbl, FORMAT(COUNT(*),0) AS cnt FROM title_crew;

\! echo "Loading title ratings for IMDb"
LOAD DATA
  LOCAL INFILE 'title.ratings.tsv'
  INTO TABLE title_rating
  FIELDS TERMINATED BY '\t'
  IGNORE 1 LINES
  (tconst, average_rating, num_votes);

SHOW WARNINGS;

SELECT 'title_rating' AS tbl, FORMAT(COUNT(*),0) AS cnt FROM title_rating;

\! echo "Loading title principals for IMDb"
LOAD DATA 
  LOCAL INFILE 'title.principals.tsv' 
  INTO TABLE title_principal
  FIELDS TERMINATED BY '\t' 
  IGNORE 1 LINES;

SHOW WARNINGS;

SELECT 'title_principal' AS tbl, FORMAT(COUNT(*),0) AS cnt FROM title_principal;
