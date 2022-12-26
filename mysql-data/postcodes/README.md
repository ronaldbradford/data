# Postcodes

This data from [GeoNames](https://geonames.org) (available under the [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/) )
is provided "as is" without warranty or any representation of accuracy, timeliness or completeness.


## Get source data

    wget https://download.geonames.org/export/zip/allCountries.zip
    wget https://download.geonames.org/export/zip/readme.txt
    unzip allCountries.zip
    mv allCountries.txt allCountries.tsv

## Define your Database Connectivity

- See [../DOCKER.md](../DOCKER.md) for a standalone local environment. The following instructions will use
this setup, however it can be easily configured for any local or cloud-based MySQL instance.

## Load Data into MySQL

    docker cp allCountries.tsv ${DB_CONTAINER}:/
    SCHEMA="postcodes"

    docker exec -i ${DB_CONTAINER}  mysql -u${DBA_USER} -p${DBA_PASSWD} --local-infile --show-warnings < 01-schema.sql
    docker exec -i ${DB_CONTAINER}  mysql -u${DBA_USER} -p${DBA_PASSWD} --local-infile --show-warnings ${SCHEMA} < 02-tables.sql
    docker exec -i ${DB_CONTAINER}  mysql -u${DBA_USER} -p${DBA_PASSWD} --local-infile --show-warnings ${SCHEMA} < 03-load.sql
