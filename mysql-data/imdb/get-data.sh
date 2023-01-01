#!/usr/bin/env bash

echo ""
echo "MySQL Curated Datasets from Ronald Bradford - https://github.com/ronaldbradford/data"
echo " * IMDb - Source data from https://imdb.com/"
echo "   Information courtesy of IMDb (https://www.imdb.com).  Used with permission for Non-Commercial Licensing"
echo ""
echo ""


FILES="name.basics.tsv.gz title.basics.tsv.gz title.akas.tsv.gz title.episode.tsv.gz title.principals.tsv.gz title.ratings.tsv.gz title.crew.tsv.gz"
for FILE in ${FILES}; do
  if [[ ! -s "${FILE}" ]]; then
    echo "Source file '${FILE}' not found, downloading..."
    wget https://datasets.imdbws.com/${FILE}
  else
    echo "Skipping download of '${FILE}' as it exists, remove to update"
  fi
done
du -sh .
ls -lh *.tsv.gz
echo "Uncompressing files"
gunzip -f *.gz
ls -lh *.tsv
