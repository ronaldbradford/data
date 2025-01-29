select profession,count(*) from name_profession group by profession order by 2 desc;
select type,count(*) from title group by type order by 2 desc;
SELECT n.name, COUNT(tp.tconst) AS total_movies FROM name n JOIN title_principal tp ON n.nconst = tp.nconst WHERE tp.category IN ('actor', 'actress') GROUP BY n.name ORDER BY total_movies DESC LIMIT 100;

