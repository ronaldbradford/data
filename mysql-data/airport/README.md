# Airport Data

This [Our Airports](https://ourairports.com/) dataset.

## Acknowledgement

Thanks to David Megginson, Founder, OurAirports.
All data is released to the Public Domain, and comes with no guarantee of accuracy or fitness for use.

Cite: https://ourairports.com/data/

## Data Summary
- TBD


## Get the source data

    ./get-data.sh


## Define your Database Connectivity

- See [../DOCKER.md](../DOCKER.md) for a standalone local environment. The following instructions will use this setup, however it can be easily configured for any local or cloud-based MySQL instance.

## Load Data into local Docker container

    ./load-docker-data.sh

If you want to load a sample of 'N' rows (where 'N' is an integer):

    SAMPLE=<n> ./load-docker-data.sh

If you want verbose debugging of the SQL statements:

    TRACE=Y ./load-docker-data.sh

## Load Data into an existing MySQL instance

When running a local mysql client connecting to an existing local MySQL instance and you have a configured $HOME/.my.cnf

    mysql --local-infile --show-warnings < install.sql

NOTE: SQL statements use the LOAD DATA command, so applicable load data configuration is necessary.


## Tables

## Example Dataset



## Data Format

See https://ourairports.com/help/data-dictionary.html
