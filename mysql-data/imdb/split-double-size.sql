insert into name select 200000000+name_id, REPLACE(nconst,'n','r'), 
       CONCAT(SUBSTRING(name, FLOOR(CHAR_LENGTH(name)/2) + 1),
       SUBSTRING(name, 1, FLOOR(CHAR_LENGTH(name)/2)),'x2') AS swapped_name, born, died, NOW() FROM name;
insert into name_profession select 100000000+name_id, profession from name_profession;
insert into name_known_for select 100000000+name_id, 100000000+title_id from name_known_for;
insert into title select 100000000+title_id, REVERSE(tconst), type, REVERSE(title), REVERSE(original_title), is_adult, start_year, end_year, run_time_mins, NOW() FROM title;
insert into title_genre select 100000000+title_id,genre from title_genre;
insert into title_rating select 100000000+title_id,average_rating, num_votes from title_rating;
insert into title_principal select 100000000+title_id,100000000+name_id,ordering, category, job, characters from title_principal;
insert into title_name_character SELECT NULL,100000000+title_id,100000000+name_id,character_name from title_name_character;
insert into title_episode SELECT 100000000+parent_title_id,100000000+title_id,season,episode from title_episode;
