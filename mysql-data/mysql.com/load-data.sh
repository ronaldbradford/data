#!/usr/bin/env bash

echo ""
echo "MySQL Curated Datasets from Ronald Bradford - https://github.com/ronaldbradford/data"
echo " * Various mysql.com example data sources - https://dev.mysql.com/doc/index-other.html"
echo "   This content is licensed to Oracle and/or is affiliates"
echo ""
echo ""

[[ -z "${AUTHENTICATION}" ]] && echo "ERROR: the 'AUTHENTICATION' variables containing -u,-p,-h for use with mysql client is required" && exit 1

# Example: export DOCKERIZE="docker exec -it ${DB_CONTAINER}"
# Example: export AUTHENTICATION="-h${CLUSTER_ENDPOINT} -u${DBA_USER} -p${DBA_PASSWD}"

MYSQL_OPTIONS="--show-warnings --local-infile"

echo "Validating MySQL configuration"
${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} -e "SELECT @@hostname, VERSION()"
if [[ $? -ne 0 ]]; then
  echo "Unable to test MySQL connection. Verify 'AUTHENTICATION' variable for credentials, and 'DOCKERIZE' if using docker"
  exit 1
fi

DATASET="world-db"
echo "Loading the '${DATASET}' dataset"
${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} < ${DATASET}/world.sql
# We have to force (-f) to get around legacy errors
DATASET="sakila-db"
echo "Loading the '${DATASET}' dataset"
${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} -f < ${DATASET}/sakila-schema.sql 
${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} < ${DATASET}/sakila-data.sql


DATASET="menagerie-db"
echo "Loading the '${DATASET}' dataset"
cd ${DATASET}
SCHEMA="menagerie"
${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} -e "DROP SCHEMA IF EXISTS ${SCHEMA}; CREATE SCHEMA ${SCHEMA}"
${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} ${SCHEMA} < cr_pet_tbl.sql
${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} ${SCHEMA} < ins_puff_rec.sql
${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} ${SCHEMA} < cr_event_tbl.sql
${DOCKERIZE} mysql ${AUTHENTICATION} ${MYSQL_OPTIONS} ${SCHEMA} < load_pet_tbl.sql
cd ..

SOURCE="airportdb"
cd airport-db
mysql ${AUTHENTICATION} < ${SOURCE}.sql
TABLE_ORDER="airport airline airplane_type airplane airport_geo airport_reachable weatherdata employee flightschedule flight flight_log passenger passengerdetails booking"
for TABLE in ${TABLE_ORDER}; do
  ${DOCKERIZE} mysql ${AUTHENTICATION} ${SOURCE} < ${SOURCE}@${TABLE}.sql
done
zstd -df *.tsv.zst
cat airportdb@booking@*.tsv > booking.tsv
sed -e "s/813/6670/;s/1418/8759/;s/452/1984/" airportdb@airline@@0.tsv > airline.tsv
