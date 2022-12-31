#!/usr/bin/env bash

FILE="allCountries.zip"
TSV_FILE="$(echo "${FILE}" | sed -e "s/.zip/.tsv/")"

echo ""
echo "MySQL Curated Datasets from Ronald Bradford - https://github.com/ronaldbradford/data"
echo " * Postcodes - Source data from https://www.geonames.org/"
echo ""
echo ""

if [ ! -s "${FILE}" ]; then
  echo "Source file '${FILE}' not found, downloading..."
  wget https://download.geonames.org/export/zip/${FILE}
  wget https://download.geonames.org/export/zip/readme.txt
  unzip ${FILE}
  mv allCountries.txt ${TSV_FILE}
else
  echo "Skipping download of '${FILE}' as it exists, remove to update"
fi

echo "Details of '${TSV_FILE}'"
ls -lh ${TSV_FILE}
wc -l ${TSV_FILE}
