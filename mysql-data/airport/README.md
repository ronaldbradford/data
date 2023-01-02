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

```
CREATE TABLE airport (
  airport_id    INT UNSIGNED NOT NULL,
  ident         VARCHAR(7) NOT NULL,
  type          VARCHAR(20) NOT NULL,
  name          VARCHAR(100) NOT NULL,
  latitude      FLOAT NOT NULL,
  longitude     FLOAT NOT NULL,
  elevation_ft  SMALLINT NULL DEFAULT NULL,
  continent     CHAR(2) NOT NULL,
  country_code  CHAR(2) NOT NULL,
  region_code   CHAR(7) NOT NULL,
  municipality  VARCHAR(60) NOT NULL,
  scheduled_service  BOOLEAN NOT NULL,
  gps_code      CHAR(4) NULL,
  iata_code     CHAR(3) NULL,
  local_code    VARCHAR(7) NULL,
  home_url      VARCHAR(128) NULL,
  wikipedia_url VARCHAR(128) NULL,
  keywords      VARCHAR(300) NULL,
  PRIMARY KEY (airport_id),
  KEY (name),
  KEY (country_code),
  KEY (region_code)
);

CREATE TABLE airport_frequency(
  frequency_id   INT UNSIGNED NOT NULL,
  airport_id     INT UNSIGNED NOT NULL,
  ident          VARCHAR(7) NOT NULL,
  type           VARCHAR(20) NOT NULL,
  description    VARCHAR(100) NOT NULL,
  frequency_mhz  DECIMAL(7,3) NOT NULL,
  PRIMARY KEY(frequency_id),
  KEY (airport_id)
);

CREATE TABLE country(
  country_id     INT UNSIGNED NOT NULL,
  country_code   CHAR(2) NOT NULL,
  name           VARCHAR(50) NOT NULL,
  continent_code CHAR(2) NOT NULL,
  wikipedia_url  VARCHAR(128) NULL,
  keywords       VARCHAR(300) NULL,
  PRIMARY KEY(country_code),
  UNIQUE KEY(country_id)
);


CREATE TABLE region(
  region_id      INT UNSIGNED NOT NULL,
  region_code    VARCHAR(7) NOT NULL,
  local_code     VARCHAR(4) NOT NULL,
  name           VARCHAR(100) NOT NULL,
  continent_code CHAR(2) NOT NULL,
  country_code   CHAR(2) NOT NULL,
  wikipedia_url  VARCHAR(128) NULL,
  keywords       VARCHAR(300) NULL,
  PRIMARY KEY(region_code),
  UNIQUE KEY(region_id)
);


CREATE TABLE continent(
  continent_code CHAR(2) NOT NULL,
  name VARCHAR(20) NOT NULL,
  PRIMARY KEY(continent_code)
);
```

## Example Dataset

```
SELECT type,COUNT(*) AS cnt
FROM airport
GROUP BY type
ORDER BY 2 DESC
--------------

+----------------+-------+
| type           | cnt   |
+----------------+-------+
| small_airport  | 39136 |
| heliport       | 18931 |
| closed         |  9990 |
| medium_airport |  4758 |
| seaplane_base  |  1129 |
| large_airport  |   462 |
| balloonport    |    45 |
+----------------+-------+

SELECT a.country_code, c.name, COUNT(*) AS cnt
FROM airport a
  INNER JOIN country c USING (country_code)
GROUP BY country_code, name
ORDER BY 3 DESC
LIMIT 10
--------------

+--------------+----------------+-------+
| country_code | name           | cnt   |
+--------------+----------------+-------+
| US           | United States  | 29821 |
| BR           | Brazil         |  6476 |
| JP           | Japan          |  3311 |
| CA           | Canada         |  2954 |
| AU           | Australia      |  2448 |
| MX           | Mexico         |  2199 |
| RU           | Russia         |  1526 |
| KR           | South Korea    |  1400 |
| GB           | United Kingdom |  1370 |
| DE           | Germany        |  1018 |
+--------------+----------------+-------+
10 rows in set (0.10 sec)
```


## Data Format

See https://ourairports.com/help/data-dictionary.html
