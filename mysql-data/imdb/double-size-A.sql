set @letter = 'A';
SELECT max(name_id) INTO @last_name_id FROM name;
SELECT max(title_id) INTO @last_title_id FROM title;
SELECT @letter, @last_name_id, @last_title_id;

INSERT INTO name SELECT @last_name_id+name_id, REPLACE(nconst,'m',@letter), CONCAT(name,' ',@letter), born+1, died+1, NOW() FROM name;
INSERT INTO name_profession SELECT @last_name_id+name_id, CONCAT(profession,' ',@letter) FROM name_profession;
INSERT INTO name_known_for SELECT @last_name_id+name_id, @last_title_id+title_id FROM name_known_for;
INSERT INTO title_name_character SELECT NULL,@last_title_id+title_id,@last_name_id+name_id,CONCAT(character_name,' ',@letter) FROM title_name_character;

INSERT INTO title SELECT @last_title_id+title_id, REPLACE(tconst,'t',@letter), CONCAT(type,@letter), CONCAT(title,' ',@letter), CONCAT(original_title,' ',@letter), is_adult, start_year+1, end_year, run_time_mins, NOW() FROM title;
INSERT INTO title_genre SELECT @last_title_id+title_id,genre FROM title_genre;
INSERT INTO title_rating SELECT @last_title_id+title_id,average_rating-0.1, num_votes+1 FROM title_rating;
INSERT INTO title_principal SELECT @last_title_id+title_id,@last_name_id+name_id,ordering, CONCAT(category,' ',@letter), CONCAT(job,' ',@letter), characters FROM title_principal;
INSERT INTO title_episode SELECT @last_title_id+parent_title_id,@last_title_id+title_id,season,episode FROM title_episode;
