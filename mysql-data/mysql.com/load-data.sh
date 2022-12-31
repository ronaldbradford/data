#!/usr/bin/env bash

echo ""
echo "MySQL Curated Datasets from Ronald Bradford - https://github.com/ronaldbradford/data"
echo " * Various mysql.com example data sources - https://dev.mysql.com/doc/index-other.html"
echo "   This content is licensed to Oracle and/or is affiliates"
echo ""
echo ""

# Example: export DOCKERIZE="docker exec -it ${DB_CONTAINER}"
# Example: export AUTHENTICATION="-h${CLUSTER_ENDPOINT} -u${DBA_USER} -p${DBA_PASSWD}"

[[ -z "${AUTHENTICATION}" ]] && echo "ERROR: the 'AUTHENTICATION' variables containing -u,-p,-h for use with mysql client is required" && exit 1
MYSQL_OPTIONS="--show-warnings --local-infile"

validate-connectivity() {
  echo "Validating MySQL configuration"
  ${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} -e "SELECT @@hostname, VERSION()"
  if [[ $? -ne 0 ]]; then
    echo "Unable to test MySQL connection. Verify 'AUTHENTICATION' variable for credentials, and 'DOCKERIZE' if using docker"
    exit 1
  fi
}

load-world-db() {
  local DATASET="world-db"

  [ ! -s "${DATASET}/world.sql" ] && echo "ERROR: run load-data.sh first" && exit 1

  echo "Loading the '${DATASET}' dataset"
  ${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} < ${DATASET}/world.sql
}

load-sakila-db() {
  local DATASET="sakila-db"

  [ ! -s "${DATASET}/sakila-schema.sql" ] && echo "ERROR: run load-data.sh first" && exit 1

  echo "Loading the '${DATASET}' dataset"
  # We have to force (-f) to get around legacy errors
  ${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} -f < ${DATASET}/sakila-schema.sql
  ${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} < ${DATASET}/sakila-data.sql
}

load-menagerie-db() {
  DATASET="menagerie-db"
  [ ! -s "${DATASET}/cr_pet_tbl.sql" ] && echo "ERROR: run load-data.sh first" && exit 1

  echo "Loading the '${DATASET}' dataset"
  cd ${DATASET}
  SCHEMA="menagerie"
  ${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} -e "DROP SCHEMA IF EXISTS ${SCHEMA}; CREATE SCHEMA ${SCHEMA}"
  ${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} ${SCHEMA} < cr_pet_tbl.sql
  ${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} ${SCHEMA} < ins_puff_rec.sql
  ${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} ${SCHEMA} < cr_event_tbl.sql
  ${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} ${SCHEMA} < load_pet_tbl.sql
  cd ..
}

load-airport-db() {
  DATASET="airportdb"
  [ ! -s "airport-db/${DATASET}.sql" ] && echo "ERROR: run load-data.sh first" && exit 1

  echo "Creating '${DATASET}' tables"
  cd airport-db  # Does not match subsequent database schema???
  mysql ${AUTHENTICATION} < ${DATASET}.sql
  TABLE_ORDER="airport airline airplane_type airplane airport_geo airport_reachable weatherdata employee flightschedule flight flight_log passenger passengerdetails booking"
  for TABLE in ${TABLE_ORDER}; do
    ${DOCKERIZE} mysql ${AUTHENTICATION} ${DATASET} < ${DATASET}@${TABLE}.sql
  done
  echo "Preparing '${DATASET}' data"
  zstd -df *.tsv.zst
  echo "Patching airline data that causes FK errors"
  sed -e "s/813/6670/;s/1418/8759/;s/452/1984/" ${DATASET}@airline@@0.tsv > airline.tsv
  echo "Consolidating all bookings to perform a single load"
  cat airportdb@booking@*.tsv > booking.tsv
  ls -lh *.tsv
  wc -l booking.tsv
  echo "Loading '${DATASET}' data"
  cp ../03-load.sql .
  ${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} ${DATASET} < 03-load.sql

}

validate-connectivity
#load-world-db
#load-sakila-db
#load-menagerie-db
load-airport-db
