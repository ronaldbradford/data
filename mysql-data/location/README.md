# Location Data

This geocoding location data has been generated using [Nominatim](https://nominatim.org/) from [OpenStreetMap Data Download](https://wiki.openstreetmap.org/wiki/Downloading_data).

## Acknowledgement

OpenStreetMap® is open data, licensed under the [Open Data Commons Open Database License](https://opendatacommons.org/licenses/odbl/) (ODbL) by the OpenStreetMap Foundation](https://osmfoundation.org/) (OSMF).

You are free to copy, distribute, transmit and adapt our data, as long as you credit OpenStreetMap and its contributors. If you alter or build upon our data, you may distribute the result only under the same licence. The full legal code explains your rights and responsibilities.

Our documentation is licensed under the Creative Commons Attribution-ShareAlike 2.0 license (CC BY-SA 2.0).

Cite: https://www.openstreetmap.org/copyright

## Data Summary
- TBD


## Get the source data

All data is included.


## Define your Database Connectivity

- See [../DOCKER.md](../DOCKER.md) for a standalone local environment. The following instructions will use this setup, however it can be easily configured for any local or cloud-based MySQL instance.

## Load Data into local Docker container

    ./load-docker-data.sh

If you want to load a sample of 'N' rows (where 'N' is an integer):

    SAMPLE=<n> ./load-docker-data.sh

If you want verbose debugging of the SQL statements:

    TRACE=Y ./load-docker-data.sh

## Load Data into an existing MySQL instance

When running a local mysql client connecting to an existing local MySQL instance and you have a configured `$HOME/.my.cnf`

    mysql --local-infile --show-warnings < install.sql

NOTE: SQL statements use the `LOAD DATA` command, so applicable load data configuration is necessary.



## Tables


    CREATE TABLE place (
      place_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
      name     JSON DEFAULT NULL,
      country_code CHAR(2) DEFAULT NULL,
      display_name VARCHAR(500) GENERATED ALWAYS AS (JSON_UNQUOTE(JSON_EXTRACT(name,_utf8mb4'$.display_name'))) VIRTUAL,
      PRIMARY KEY (place_id),
      KEY country_code (country_code),
      KEY display_name (display_name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


## Example Dataset

    SELECT country_code, COUNT(*) AS cnt
    FROM place
    GROUP BY country_code
    ORDER BY 2 DESC
    LIMIT 20
    --------------

    +--------------+-------+
    | country_code | cnt   |
    +--------------+-------+
    | GB           | 10193 |
    | CN           |  7262 |
    | PL           |  7054 |
    | AU           |  4993 |
    | ID           |  4109 |
    | IN           |  2807 |
    | CZ           |  2787 |
    | BR           |  2576 |
    | RU           |  2347 |
    | PH           |  2257 |
    | DE           |  2032 |
    | FR           |  1898 |
    | TR           |  1713 |
    | JP           |  1517 |
    | SE           |  1449 |
    | PT           |  1351 |
    | US           |  1328 |
    | LK           |  1203 |
    | NG           |  1170 |
    | ES           |  1082 |
    +--------------+-------+
    20 rows in set (0.02 sec)

    SELECT country_code, COUNT(*) AS cnt
    FROM place
    GROUP BY country_code
    ORDER BY 2 ASC
    LIMIT 20
    --------------

    +--------------+-----+
    | country_code | cnt |
    +--------------+-----+
    | ST           |   1 |
    | VG           |   1 |
    | NU           |   1 |
    | PN           |   1 |
    | SH           |   1 |
    | TC           |   1 |
    | RO           |   1 |
    | FK           |   2 |
    | TK           |   2 |
    | CK           |   2 |
    | MS           |   3 |
    | NR           |   4 |
    | TO           |   4 |
    | SM           |   4 |
    | GS           |   4 |
    | SB           |   4 |
    | TV           |   4 |
    | SK           |   4 |
    | SC           |   4 |
    | AI           |   4 |
    +--------------+-----+
    20 rows in set (0.02 sec)

    SELECT JSON_UNQUOTE(name->'$.lat') as latitude,  
           JSON_UNQUOTE(name->'$.lon') AS longitude,
          JSON_UNQUOTE(name->'$.address') AS address,
          ST_GeomFromText(CONCAT('POINT(',JSON_UNQUOTE(name->'$.lat'),' ',JSON_UNQUOTE(name->'$.lon'),')'), 4326) AS geo,
          ST_AsGeoJSON(ST_GeomFromText(CONCAT('POINT(',JSON_UNQUOTE(name->'$.lat'),' ',JSON_UNQUOTE(name->'$.lon'),')'), 4326)) AS geoJSON
    FROM place
    WHERE country_code = 'AU'
    AND JSON_UNQUOTE(name->'$.address.state') = 'Queensland'
    LIMIT 2\G

    *************************** 1. row ***************************
    latitude: -27.62514435
    longitude: 152.96828219799434
    address: {"road": "Forest Lake Boulevard", "shop": "Forest Lake Shopping Centre", "state": "Queensland", "suburb": "Forest Lake", "country": "Australia", "district": "Greater Brisbane", "postcode": "4078", "country_code": "au", "house_number": "235", "city_district": "Forest Lake", "neighbourhood": "Greentree Pocket", "ISO3166-2-lvl4": "AU-QLD"}
      geo: 0xE61000000101000000E9B5F22AFC1E63407887CA7509A03BC0
    geoJSON: {"type": "Point", "coordinates": [152.96828219799434, -27.62514435]}
    *************************** 2. row ***************************
    latitude: -27.46807545
    longitude: 153.0281884548271
    address: {"city": "Brisbane City", "road": "Queen Street", "state": "Queensland", "suburb": "Brisbane City", "amenity": "General Post Office", "country": "Australia", "postcode": "4000", "country_code": "au", "house_number": "261", "city_district": "Brisbane City", "ISO3166-2-lvl4": "AU-QLD"}
      geo: 0xE610000001010000006E7379EBE62063407CCFEDCAD3773BC0
    geoJSON: {"type": "Point", "coordinates": [153.0281884548271, -27.46807545]}
    2 rows in set (0.01 sec)
