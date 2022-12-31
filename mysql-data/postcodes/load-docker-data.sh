#!/usr/bin/env bash

TMP_DIR=${TMP_DIR:-/tmp}
[ -n "${TRACE}" ] && DB_VERBOSE='-vvv'
FILE="allCountries.tsv"
TARGET_FILE="${FILE}"

echo ""
echo "MySQL Curated Datasets from Ronald Bradford - https://github.com/ronaldbradford/data"
echo " * Postcodes - Source data from https://www.geonames.org/"
echo ""
echo ""

if [ -n "${SAMPLE}" ]; then
  SAMPLE_FILE="${TMP_DIR}/$0.$$.tsv"
  shuf -n ${SAMPLE} -o ${SAMPLE_FILE} ${FILE}
  FILE="${SAMPLE_FILE}"
  echo "Overridding data with '${FILE}' containing $(cat ${FILE} | wc -l) rows"
fi
  
echo "Preparing '${DB_CONTAINER}' container"
docker cp ${FILE} ${DB_CONTAINER}:/${TARGET_FILE}
for file in $(ls *.sql); do docker cp $file ${DB_CONTAINER}:/; done

echo "Installing dataset"
docker exec -i ${DB_CONTAINER}  mysql -u${DBA_USER} -p${DBA_PASSWD} --local-infile --show-warnings ${DB_VERBOSE} < install.sql
