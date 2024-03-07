time mysqldump --add-drop-database --add-drop-table --complete-insert --single-transaction --dump-date --triggers imdb | gzip - >  imdb.$(date +%Y-%m-%d).sql.gz
