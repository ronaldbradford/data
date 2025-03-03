#!/usr/bin/env bash

YEAR=${YEAR:-2022}
START=${START:-1}
END=${END:-12}

for MONTH in $(seq -w ${START} ${END}); do
    echo "Processing ${YEAR}-${MONTH}"
    FILE="yellow_tripdata_${YEAR}-${MONTH}"
    if [ ! -n "${FILE}" ]; then
      echo "Getting '${FILE}.parquet'"
      wget https://d37ci6vzurychx.cloudfront.net/trip-data/${FILE}.parquet
    fi
    ./convert.py ${FILE}.parquet
    wc -l ${FILE}.tsv
    ./slow-insert.sh ${FILE}.tsv
done
