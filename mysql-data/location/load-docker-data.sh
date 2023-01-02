#!/usr/bin/env bash

TMP_DIR=${TMP_DIR:-/tmp}
[ -n "${TRACE}" ] && DB_VERBOSE='-vvv'
FILE="location.json"

echo ""
echo "MySQL Curated Datasets from Ronald Bradford - https://github.com/ronaldbradford/data"
echo " * Locations"
echo "   OpenStreetMap® is open data, licensed under the pen Data Commons Open Database License. See https://www.openstreetmap.org/copyright"
echo ""
echo ""

[ ! -s "${FILE}" ] && gunzip ${FILE}.gz

if [ -n "${SAMPLE}" ]; then
  echo "Sampling '${SAMPLE}' rows"
  [[ ! -f "${FILE}.all" ]] && mv ${FILE} ${FILE}.all
  SAMPLE_FILE="${TMP_DIR}/$0.$$.json"
  shuf -n ${SAMPLE} -o ${SAMPLE_FILE} ${FILE}.all
  mv ${SAMPLE_FILE} ${FILE}
  echo "Overridding '${FILE}' data containing $(cat ${FILE} | wc -l) rows"
fi
  
echo "Preparing '${DB_CONTAINER}' container"
docker cp ${FILE} ${DB_CONTAINER}:/
for file in $(ls *.sql); do docker cp $file ${DB_CONTAINER}:/; done

echo "Installing dataset"
docker exec -i ${DB_CONTAINER}  mysql -u${DBA_USER} -p${DBA_PASSWD} --local-infile --show-warnings -t ${DB_VERBOSE} < install.sql
