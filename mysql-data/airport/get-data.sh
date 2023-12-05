#!/usr/bin/env bash

echo ""
echo "MySQL Curated Datasets from Ronald Bradford - https://github.com/ronaldbradford/data"
echo " * airports - Source data from https://ourairports.com"
echo "   All data is released to the Public Domain, and comes with no guarantee of accuracy or fitness for use."
echo ""
echo ""



FILES="airports countries regions airport-frequencies runways navaids airport-comments"

for FILE in ${FILES}; do
  CSV_FILE="${FILE}.csv"
  if [ ! -s "${CSV_FILE}" ]; then
    echo "Getting '${CSV_FILE}'"
    wget https://davidmegginson.github.io/ourairports-data/${CSV_FILE}
  else
    echo "Using exsting '${CSV_FILE}'"
  fi
  head -1 ${CSV_FILE}
  wc -l ${CSV_FILE}
done

ls -lh *.csv
wc -l *.csv
