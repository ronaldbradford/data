# MySQL.com example datasets

These are 4 example datasets available at [MySQL.com Example Datasets](https://dev.mysql.com/doc/index-other.html)
 - [Sakila](https://dev.mysql.com/doc/sakila/en/)
 - [World](https://dev.mysql.com/doc/world-setup/en/)
 - Menagerie
 - [Airport](https://dev.mysql.com/doc/airportdb/en/)

## Download

  ./get-data.sh

## Installation

  export AUTHENTICATION="-u<user> -p<password> -h<host>"
  ./load-data.sh

If you wish to use with a docker container, created for example with this repos [Docker Setup](../DOCKER.md).

  source .db.cnf
  export DOCKERIZE=
  export AUTHENTICATION="-u<user> -p<password> -h<host>"
  ./load-data.sh
  
