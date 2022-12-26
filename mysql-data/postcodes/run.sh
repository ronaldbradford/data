#!/usr/bin/env bash

. ../.db.conf
echo "[mysql]
user=${DBA_USER}
password=${DBA_PASSWD}
local_infile=1
show_warnings=1" > .my.cnf


docker cp .my.cnf ${DB_CONTAINER}:/root

export SCHEMA=postcodes

#database=postcodes

docker exec -i ${DB_CONTAINER} mysql < drop.sql
docker exec -i ${DB_CONTAINER} mysql < 01-schema.sql
docker exec -i ${DB_CONTAINER} mysql ${SCHEMA} < 02-tables.sql
docker exec -i ${DB_CONTAINER} mysql ${SCHEMA} < 03-load.sql


cat drop.sql ??-*.sql > all.sql
