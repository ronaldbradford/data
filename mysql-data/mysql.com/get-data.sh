#!/usr/bin/env bash

echo ""
echo "MySQL Curated Datasets from Ronald Bradford - https://github.com/ronaldbradford/data"
echo " * Various mysql.com example data sources - https://dev.mysql.com/doc/index-other.html"
echo "   This content is licensed to Oracle and/or is affiliates"
echo ""
echo ""

MYSQL_SOURCES="world-db.tar.gz sakila-db.tar.gz menagerie-db.tar.gz airport-db.tar.gz"
for FILE in ${MYSQL_SOURCES}; do
  if [[ ! -s "${FILE}" ]]; then
    echo "Source '${FILE}' not found, downloading..."
    wget https://downloads.mysql.com/docs/${FILE}
  else
    echo "Skipping download of '${FILE}' as it exists, remove to update"
  fi
  ls -lh ${FILE}
  tar xfz ${FILE}
  du -sh $(cut -d. -f1 <<< ${FILE})
done
