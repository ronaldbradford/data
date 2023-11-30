# MySQL Curated DataSets

These datasets are designed for use with a RDBMS. Ideally future goals are to enable
the ability to load data into different products for evaluation.  At this time MySQL syntax is provided.

## My Curated DataSets
- [Postcodes](postcodes/README.md) (1,549,815 postal codes, 96 countries)
- [NYC Yellow Taxi Rides](nyc-taxi/README.md) (246k rows - Jan 2022 example)
- [IMDb](imdb/README.md) (12,188,623 names)
- [High Accuracy Locations](mysql-data/location/README.md) (90k places from 216 countries)
- [Airports](mysql-data/airports/README.md) (74,451 airports)

## Other MySQL DataSets

These datasets have been created by other parties and contain table structures, data files and loading instructions for MySQL usage.

### mysql.com
- [MySQL.com Example Datasets](https://dev.mysql.com/doc/index-other.html)
 - [Sakila](https://dev.mysql.com/doc/sakila/en/)
 - [World](https://dev.mysql.com/doc/world-setup/en/)
 - Menagerie
 - [Airport](https://dev.mysql.com/doc/airportdb/en/) (54,304,619 bookings)

These MySQL sources are designed to all be loaded as one example using included scripts. See [instructions](mysql.com/README.md). The full data is not provided here, however a script that downloads the data is available.

The mysql.com airport dataset is actually derived from [Flughafen DB](https://github.com/stefanproell/flughafendb/) created by [Stefan Proell](https://www.stefanproell.at/).

### DataCharmer
  - [Employees](https://dev.mysql.com/doc/airportdb/en/) [GitHub](https://github.com/datacharmer/test_db)

See [instructions](datacharmer/README.md) for installation.
