# Country Postcodes Dataset (96+ countries)

This data from [GeoNames](https://geonames.org) \(available under the [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/) )
is provided "as is" without warranty or any representation of accuracy, timeliness or completeness.

## Data Summary

As at 2022-12-26 22:05:36

- 96 Countries
- 1,549,815 Postal Codes
- 2 tables (postcode, postcode_geo)
- Top Countries (Portugal, India, Japan, Mexico)
- US Postcodes 41,483
- Australia Postcodes 16,873
- Great Britian Postcodes 27,430

### Did you know

[American Samoa](https://www.google.com/maps/place/American+Samoa/@-37.8265655,-164.1712804,4.27z/data=!4m5!3m4!1s0x71a684b79248fdc9:0xf3ee739e2dae4bdd!8m2!3d-14.270972!4d-170.132217), Vatican City and [Palau](https://www.google.com/maps/place/Palau/@-13.1335443,146.6204552,4.78z/data=!4m5!3m4!1s0x328445b4a2af0399:0x12ed1edd39a1ebbb!8m2!3d7.51498!4d134.58252) hold the record of containing just 1 postcode for the country (with this dataset).

## Get source data used in this example

    ./get-data.sh

A sample file `demo.tsv` contains a subset of data that can be used if you do not wish to download the full data. This has to renamed to `allCountries.tsv` to use.

## Define your Database Connectivity

- See [../DOCKER.md](../DOCKER.md) for a standalone local environment. The following instructions will use
this setup, however steps can be easily configured for any local or cloud-based MySQL instance.

## Load Data into an existing MySQL instance

When running a local mysql client connecting to an existing local MySQL instance and you have a configured `$HOME/.my.cnf`

    mysql --local-infile --show-warnings < install.sql

NOTE: SQL statements use the `LOAD DATA` command, so applicable load data configuration is necessary.

### Loading data into local Docker container

    ./load-docker-data.sh

If you want to load a sample of 'N' rows (where 'N' is an integer):

    SAMPLE=<n> ./load-docker-data.sh

If you want verbose debugging of the SQL statements:

    TRACE=Y ./load-docker-data.sh

## Tables in this dataset

- postcode
- postcode_geo

```
    CREATE TABLE postcode (
      postcode_id int unsigned NOT NULL AUTO_INCREMENT,
      country_code char(2) NOT NULL,
      postal_code varchar(20) NOT NULL,
      place_name varchar(180) NOT NULL,
      admin_name1 varchar(100) DEFAULT NULL,
      admin_code1 varchar(20) DEFAULT NULL,
      admin_name2 varchar(100) DEFAULT NULL,
      admin_code2 varchar(20) DEFAULT NULL,
      admin_name3 varchar(100) DEFAULT NULL,
      admin_code3 varchar(20) DEFAULT NULL,
      lat float NOT NULL,
      lng float NOT NULL,
      accuracy tinyint unsigned DEFAULT NULL,
      PRIMARY KEY (postcode_id),
      KEY country_code (country_code,postal_code),
      KEY lat (lat,lng)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

    CREATE TABLE postcode_geo (
      postcode_id int unsigned NOT NULL AUTO_INCREMENT,
      country_code char(2) NOT NULL,
      postal_code varchar(20) NOT NULL,
      location point NOT NULL /*!80003 SRID 0 */,
      PRIMARY KEY (postcode_id),
      SPATIAL KEY location (location)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

## Example Queries of Dataset


    mysql> SELECT COUNT(DISTINCT country_code) AS country_count FROM postcode;
    +---------------+
    | country_count |
    +---------------+
    |            96 |
    +---------------+
    1 row in set (0.01 sec)

    mysql> SELECT COUNT(*) AS australia_count FROM postcode WHERE country_code='AU';
    +-----------------+
    | australia_count |
    +-----------------+
    |           16873 |
    +-----------------+
    1 row in set (0.01 sec)

    MySQL> SELECT COUNT(*) AS us_count FROM postcode WHERE country_code='US';
    +----------+
    | us_count |
    +----------+
    |    41483 |
    +----------+
    1 row in set (0.01 sec)

    mysql> SELECT * FROM postcode WHERE country_code='AU' AND postal_code='4370';
    +-------------+--------------+-------------+-------------------+-------------+-------------+------------------+-------------+-------------+-------------+----------+---------+----------+
    | postcode_id | country_code | postal_code | place_name        | admin_name1 | admin_code1 | admin_name2      | admin_code2 | admin_name3 | admin_code3 | lat      | lng     | accuracy |
    +-------------+--------------+-------------+-------------------+-------------+-------------+------------------+-------------+-------------+-------------+----------+---------+----------+
    |       45892 | AU           | 4370        | Murrays Bridge    | Queensland  | QLD         |                  |             |             |             | -28.3096 | 152.116 |        3 |
    |       45893 | AU           | 4370        | Allan             | Queensland  | QLD         |                  |             |             |             | -28.1937 | 151.952 |        4 |
    |       45894 | AU           | 4370        | Wiyarra           | Queensland  | QLD         |                  |             |             |             |  -28.275 | 152.209 |        4 |
    |       45895 | AU           | 4370        | Gladfield         | Queensland  | QLD         |                  |             |             |             | -28.0735 | 152.184 |        3 |
    |       45896 | AU           | 4370        | Rodgers Creek     | Queensland  | QLD         |                  |             |             |             | -28.2286 | 151.825 |        3 |
    |       45897 | AU           | 4370        | Upper Wheatvale   | Queensland  | QLD         |                  |             |             |             | -28.1385 | 151.872 |        3 |
    |       45898 | AU           | 4370        | Wildash           | Queensland  | QLD         |                  |             |             |             | -28.3336 | 152.055 |        3 |
    |       45899 | AU           | 4370        | Tregony           | Queensland  | QLD         |                  |             |             |             | -28.0601 | 152.314 |        3 |
    |       45900 | AU           | 4370        | Glengallan        | Queensland  | QLD         |                  |             |             |             | -28.1033 | 152.068 |        3 |
    |       45901 | AU           | 4370        | Thanes Creek      | Queensland  | QLD         |                  |             |             |             | -28.1174 | 151.675 |        4 |
    |       45902 | AU           | 4370        | The Glen          | Queensland  | QLD         |                  |             |             |             | -28.3397 | 151.928 |        4 |
    |       45903 | AU           | 4370        | Elbow Valley      | Queensland  | QLD         |                  |             |             |             | -28.4102 | 152.155 |        4 |
    |       45904 | AU           | 4370        | Cunningham        | Queensland  | QLD         |                  |             |             |             | -28.1712 | 151.826 |        4 |
    |       45905 | AU           | 4370        | Wheatvale         | Queensland  | QLD         |                  |             |             |             | -28.1647 | 151.872 |        4 |
    |       45906 | AU           | 4370        | Loch Lomond       | Queensland  | QLD         |                  |             |             |             | -28.3237 | 152.186 |        4 |
    |       45907 | AU           | 4370        | Clintonvale       | Queensland  | QLD         |                  |             |             |             | -28.0999 | 152.118 |        4 |
    |       45908 | AU           | 4370        | Warwick DC        | Queensland  | QLD         |                  |             |             |             | -28.1853 |  152.02 |        3 |
    |       45909 | AU           | 4370        | Swan Creek        | Queensland  | QLD         |                  |             |             |             | -28.2022 | 152.143 |        4 |
    |       45910 | AU           | 4370        | Morgan Park       | Queensland  | QLD         |                  |             |             |             | -28.2492 | 152.039 |        4 |
    |       45911 | AU           | 4370        | Greymare          | Queensland  | QLD         |                  |             |             |             | -28.2136 | 151.751 |        4 |
    |       45912 | AU           | 4370        | Mount Colliery    | Queensland  | QLD         |                  |             |             |             | -28.2797 | 152.308 |        4 |
    |       45913 | AU           | 4370        | Mount Sturt       | Queensland  | QLD         |                  |             |             |             | -28.1678 | 152.207 |        4 |
    |       45914 | AU           | 4370        | Leslie            | Queensland  | QLD         |                  |             |             |             | -28.1706 | 151.912 |        4 |
    |       45915 | AU           | 4370        | Upper Freestone   | Queensland  | QLD         |                  |             |             |             | -28.1311 | 152.211 |        4 |
    |       45916 | AU           | 4370        | Willowvale        | Queensland  | QLD         |                  |             |             |             | -28.1346 | 152.032 |        3 |
    |       45917 | AU           | 4370        | Mount Tabor       | Queensland  | QLD         |                  |             |             |             | -28.2067 | 152.068 |        3 |
    |       45918 | AU           | 4370        | Leslie Dam        | Queensland  | QLD         |                  |             |             |             | -28.2408 | 151.913 |        3 |
    |       45919 | AU           | 4370        | The Hermitage     | Queensland  | QLD         |                  |             |             |             | -28.2056 | 152.107 |        3 |
    |       45920 | AU           | 4370        | Rosenthal Heights | Queensland  | QLD         |                  |             |             |             | -28.2316 | 151.995 |        4 |
    |       45921 | AU           | 4370        | Montrose          | Queensland  | QLD         |                  |             |             |             |  -28.162 | 151.775 |        4 |
    |       45922 | AU           | 4370        | Danderoo          | Queensland  | QLD         |                  |             |             |             | -28.2536 |  152.23 |        4 |
    |       45923 | AU           | 4370        | Warwick           | Queensland  | QLD         | TOOWOOMBA SE CNR |             |             |             | -28.2174 | 152.029 |        4 |
    |       45924 | AU           | 4370        | Silverwood        | Queensland  | QLD         |                  |             |             |             | -28.3441 | 152.012 |        4 |
    |       45925 | AU           | 4370        | Cherry Gully      | Queensland  | QLD         |                  |             |             |             | -28.4174 |  152.06 |        4 |
    |       45926 | AU           | 4370        | Toolburra         | Queensland  | QLD         |                  |             |             |             | -28.1706 | 151.968 |        4 |
    |       45927 | AU           | 4370        | Massie            | Queensland  | QLD         |                  |             |             |             | -28.1381 |  151.94 |        4 |
    |       45928 | AU           | 4370        | Thane             | Queensland  | QLD         |                  |             |             |             |  -28.157 | 151.704 |        4 |
    |       45929 | AU           | 4370        | North Branch      | Queensland  | QLD         |                  |             |             |             | -28.0228 | 152.299 |        4 |
    |       45930 | AU           | 4370        | Freestone         | Queensland  | QLD         |                  |             |             |             |  -28.132 | 152.152 |        4 |
    |       45931 | AU           | 4370        | Womina            | Queensland  | QLD         |                  |             |             |             | -28.1909 | 152.037 |        4 |
    |       45932 | AU           | 4370        | Maryvale          | Queensland  | QLD         | TOOWOOMBA SE CNR |             |             |             | -28.0731 | 152.244 |        4 |
    |       45933 | AU           | 4370        | Canningvale       | Queensland  | QLD         |                  |             |             |             | -28.2474 |  152.07 |        4 |
    |       45934 | AU           | 4370        | Rosehill          | Queensland  | QLD         |                  |             |             |             | -28.1851 |     152 |        4 |
    |       45935 | AU           | 4370        | Pratten           | Queensland  | QLD         |                  |             |             |             | -28.0864 |  151.78 |        4 |
    |       45936 | AU           | 4370        | Bony Mountain     | Queensland  | QLD         |                  |             |             |             | -28.1219 | 151.841 |        4 |
    |       45937 | AU           | 4370        | Junabee           | Queensland  | QLD         |                  |             |             |             | -28.2468 | 152.148 |        4 |
    |       45938 | AU           | 4370        | Sladevale         | Queensland  | QLD         |                  |             |             |             |  -28.186 | 152.072 |        4 |
    +-------------+--------------+-------------+-------------------+-------------+-------------+------------------+-------------+-------------+-------------+----------+---------+----------+
    47 rows in set (0.00 sec)

    mysql> SELECT * FROM postcode WHERE country_code='US' AND postal_code='90210';
    +-------------+--------------+-------------+---------------+-------------+-------------+-------------+-------------+-------------+-------------+---------+----------+----------+
    | postcode_id | country_code | postal_code | place_name    | admin_name1 | admin_code1 | admin_name2 | admin_code2 | admin_name3 | admin_code3 | lat     | lng      | accuracy |
    +-------------+--------------+-------------+---------------+-------------+-------------+-------------+-------------+-------------+-------------+---------+----------+----------+
    |     1505328 | US           | 90210       | Beverly Hills | California  | CA          | Los Angeles | 037         |             |             | 34.0901 | -118.407 |        4 |
    +-------------+--------------+-------------+---------------+-------------+-------------+-------------+-------------+-------------+-------------+---------+----------+----------+
    1 row in set (0.00 sec)

    mysql> SELECT country_code, COUNT(*) AS country_count
    -> FROM postcode
    -> GROUP BY country_code
    -> ORDER BY 2 DESC
    -> LIMIT 10;
    +--------------+---------------+
    | country_code | country_count |
    +--------------+---------------+
    | PT           |        206942 |
    | IN           |        155570 |
    | JP           |        146916 |
    | MX           |        144655 |
    | SG           |        121154 |
    | PE           |         96943 |
    | PL           |         72900 |
    | FR           |         51670 |
    | RU           |         43538 |
    | US           |         41483 |
    +--------------+---------------+
    10 rows in set (1.17 sec)
