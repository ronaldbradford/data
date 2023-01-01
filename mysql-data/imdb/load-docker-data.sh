#!/usr/bin/env bash

TMP_DIR=${TMP_DIR:-/tmp}
[ -n "${TRACE}" ] && DB_VERBOSE='-vvv'

FILES="name.basics title.akas title.basics title.crew title.episode title.principals title.ratings"

echo ""
echo "MySQL Curated Datasets from Ronald Bradford - https://github.com/ronaldbradford/data"
echo " * IMDb - Source data from https://imdb.com/"
echo "   Information courtesy of IMDb (https://www.imdb.com).  Used with permission for Non-Commercial Licensing"
echo ""
echo ""

if [ -n "${SAMPLE}" ]; then
  echo "Sampling '${SAMPLE}' rows"
  for FILE in ${FILES}; do
    TSV_FILE="${FILE}.tsv"
    [[ ! -f "${TSV_FILE}.all" ]] && mv ${TSV_FILE} ${TSV_FILE}.all
    SAMPLE_FILE="${TMP_DIR}/$0.$$.tsv"
    sed -e "1d" ${TSV_FILE}.all | shuf -n ${SAMPLE} -o ${SAMPLE_FILE}
    head -1 ${TSV_FILE}.all > ${TSV_FILE}
    cat ${SAMPLE_FILE} >> ${TSV_FILE}
    rm -f ${SAMPLE_FILE}
    echo "Overridding '${TSV_FILE}' data containing $(cat ${TSV_FILE} | wc -l) rows"
  done
fi
  
echo "Preparing '${DB_CONTAINER}' container"
for FILE in ${FILES}; do
  docker cp ${FILE}.tsv ${DB_CONTAINER}:/
done
for file in $(ls *.sql); do docker cp $file ${DB_CONTAINER}:/; done

echo "Installing dataset"
docker exec -i ${DB_CONTAINER}  mysql -u${DBA_USER} -p${DBA_PASSWD} --local-infile --show-warnings -t ${DB_VERBOSE} < install.sql
