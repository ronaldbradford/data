SELECT max(name_id) INTO @last_name_id FROM name;
SELECT max(title_id) INTO @last_title_id FROM title;
SELECT @last_name_id, @last_title_id;

INSERT INTO name SELECT @last_name_id+name_id, REPLACE(nconst,'n','r'), 
       CONCAT(SUBSTRING(name, FLOOR(CHAR_LENGTH(name)/2) + 1),
       SUBSTRING(name, 1, FLOOR(CHAR_LENGTH(name)/2)),'x2') AS swapped_name, born, died, NOW() FROM name;
INSERT INTO name_profession SELECT @last_name_id+name_id, profession FROM name_profession;
INSERT INTO name_known_for SELECT @last_name_id+name_id, @last_title_id+title_id FROM name_known_for;
INSERT INTO title_name_character SELECT NULL,@last_title_id+title_id,@last_name_id+name_id,character_name FROM title_name_character;

INSERT INTO title SELECT @last_title_id+title_id, REPLACE(tconst,'tt','tr'), type, 
       CONCAT(SUBSTRING(title, FLOOR(CHAR_LENGTH(title)/2) + 1),
       SUBSTRING(title, 1, FLOOR(CHAR_LENGTH(title)/2)),'x2') AS swapped_title,
       original_title, is_adult, start_year, end_year, run_time_mins, NOW() FROM title;
INSERT INTO title_genre SELECT @last_title_id+title_id,genre FROM title_genre;
INSERT INTO title_rating SELECT @last_title_id+title_id,average_rating, num_votes FROM title_rating;
INSERT INTO title_principal SELECT @last_title_id+title_id,@last_name_id+name_id,ordering, category, job, characters FROM title_principal;
INSERT INTO title_episode SELECT @last_title_id+parent_title_id,@last_title_id+title_id,season,episode FROM title_episode;
