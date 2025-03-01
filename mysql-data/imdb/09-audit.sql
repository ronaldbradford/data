SET SESSION sql_mode='';
SELECT CURDATE(),
       LENGTH(professions) - LENGTH(REPLACE(professions, ',', ''))+1 AS professions_count,
       MAX(LENGTH(professions)) professions_length,
       LENGTH(known_for) - LENGTH(REPLACE(known_for, ',', ''))+1 AS known_for_count,
       MAX(LENGTH(known_for)) AS known_for_length
FROM   name;

SELECT MAX(LENGTH(directors)),
       MAX(LENGTH(writers)) 
FROM title_crew;

SELECT MAX(LENGTH(directors) - LENGTH(REPLACE(directors,',','')))+1 AS director_count FROM title_crew;
SELECT MAX(LENGTH(writers) - LENGTH(REPLACE(writers,',','')))+1 AS writer_count FROM title_crew;
