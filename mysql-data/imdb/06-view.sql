CREATE OR REPLACE VIEW characters AS
SELECT n.name,
       t.title,
       t.type,
       tnc.character_name,
       tnc.name_id,
       tnc.title_id
FROM   title_name_character tnc
INNER JOIN name n USING (name_id)
INNER JOIN title t USING (title_id)
WHERE  t.type != 'tvEpisode'
UNION
SELECT n.name AS name,
       CONCAT(pt.title,' - ', t.title) AS title,
       t.type,
       tnc.character_name,
       tnc.name_id,
       tnc.title_id
FROM   title_name_character tnc
INNER JOIN name n USING (name_id)
INNER JOIN title t USING (title_id)
INNER JOIN title_episode te USING (title_id)
INNER JOIN title pt ON te.parent_title_id = pt.title_id
WHERE t.type = 'tvEpisode';

CREATE OR REPLACE VIEW popular_titles AS
SELECT n.name,
       t.title,
       t.type,
       n.name_id,
       t.title_id
FROM   name_known_for kf
INNER JOIN name n USING (name_id)
INNER JOIN title t USING (title_id);
