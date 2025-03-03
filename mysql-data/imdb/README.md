# IMDb Data

This [IMDb Datasets](https://www.imdb.com/interfaces/) are Subsets of IMDb data are available for access to customers for personal and non-commercial use. You can hold local copies of this data, and it is subject to our terms and conditions.

## Acknowledgement

Information courtesy of
IMDb
(https://www.imdb.com).
Used with permission.

Cite: [Non-Commercial Licensing](https://help.imdb.com/article/imdb/general-information/can-i-use-imdb-data-in-my-software/G5JTRESSHJBBHTGX#)

## Data Summary

This is an enhanced dataset of the source IMDb Data.

Table Rows as at 3/25
```
+----------------------+------------+
| tbl                  | row_count  |
+----------------------+------------+
| credit               | 13         |
| genre                | 28         |
| name                 | 14,217,591 |
| name_known_for       | 22,879,498 |
| name_profession      | 15,836,216 |
| title                | 11,114,744 |
| title_episode        | 8,586,454  |
| title_genre          | 17,379,973 |
| title_name_character | 43,542,978 |
| title_principal      | 89,597,253 |
| title_rating         | 1,515,368  |
+----------------------+------------+
```

Schema size via Information Schema
```
+-------------------+----------------+----------------+---------------+--------+------------+
| TABLE_SCHEMA      | total_mb       | data_mb        | index_mb      | tables | today      |
+-------------------+----------------+----------------+---------------+--------+------------+
| imdb              | 21421.31250000 | 12945.53125000 | 8475.78125000 |     13 | 2025-03-01 |
```

Table sizes via Information Schema. NOTE: TABLE_ROWS is an estimate.
```
+----------------------+--------+---------+------------+---------+----------+---------+----------+
| table_name           | ENGINE | format  | TABLE_ROWS | avg_row | total_mb | data_mb | index_mb |
+----------------------+--------+---------+------------+---------+----------+---------+----------+
| title_principal      | InnoDB | Dynamic |   88728950 |      74 |  8728.00 | 6267.00 |  2461.00 |
| title_name_character | InnoDB | Dynamic |   42324654 |      45 |  5012.00 | 1838.00 |  3174.00 |
| title                | InnoDB | Dynamic |   10849309 |     117 |  1834.83 | 1211.98 |   622.84 |
| name                 | InnoDB | Dynamic |   14122805 |      66 |  1591.92 |  890.98 |   700.94 |
| name_known_for       | InnoDB | Dynamic |   23406367 |      32 |  1265.00 |  719.00 |   546.00 |
| title_episode        | InnoDB | Dynamic |    8618171 |      94 |  1130.97 |  773.97 |   357.00 |
| name_profession      | InnoDB | Dynamic |   15723311 |      39 |   918.00 |  598.00 |   320.00 |
| title_genre          | InnoDB | Dynamic |   17002325 |      37 |   896.00 |  602.00 |   294.00 |
| title_rating         | InnoDB | Dynamic |    1513187 |      30 |    44.56 |   44.56 |     0.00 |
| credit               | InnoDB | Dynamic |         13 |    1260 |     0.02 |    0.02 |     0.00 |
| genre                | InnoDB | Dynamic |         28 |     585 |     0.02 |    0.02 |     0.00 |
| characters           | NULL   | NULL    |       NULL |    NULL |     NULL |    NULL |     NULL |
| popular_titles       | NULL   | NULL    |       NULL |    NULL |     NULL |    NULL |     NULL |
+----------------------+--------+---------+------------+---------+----------+---------+----------+
```


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


## Limitations

If you have Binary Logging enabled, then `log_bin_trust_function_creators` must be 1.  See https://dev.mysql.com/doc/refman/5.7/en/replication-options-binary-log.html#sysvar_log_bin_trust_function_creators


## Tables

See 02-tables.sql for most current structure.

```
    CREATE TABLE name (
      name_id int unsigned NOT NULL AUTO_INCREMENT,
      nconst char(10) NOT NULL,
      name varchar(120) NOT NULL,
      birth_year year DEFAULT NULL,
      death_year year DEFAULT NULL,
      profession varchar(64) DEFAULT NULL, //normalized to name_profession
      known_for varchar(80) DEFAULT NULL, //TODO normalized
      PRIMARY KEY (name_id),
      UNIQUE KEY nconst (nconst)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

    CREATE TABLE title (
      title_id int unsigned NOT NULL AUTO_INCREMENT,
      tconst char(10) NOT NULL,
      type varchar(10) NOT NULL,
      title varchar(300) NOT NULL,
      original_title varchar(300) NOT NULL,
      is_adult tinyint(1) NOT NULL,
      start_year year DEFAULT NULL,
      end_year year DEFAULT NULL,
      run_time_mins smallint DEFAULT NULL,
      genres varchar(32) DEFAULT NULL, // normalized title_genre
      PRIMARY KEY (title_id),
      UNIQUE KEY tconst (tconst)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

    CREATE TABLE title_crew (
      crew_id int unsigned NOT NULL AUTO_INCREMENT,
      tconst char(10) NOT NULL,
      directors text,          // normalized to title_director
      writers text,
      PRIMARY KEY (crew_id),
      KEY tconst (tconst)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

    CREATE TABLE title_episode (
      tconst char(10) NOT NULL,
      parent_tconst char(10) NOT NULL,
      season smallint unsigned DEFAULT NULL,
      episode mediumint unsigned DEFAULT NULL,
      PRIMARY KEY (tconst,parent_tconst),
      KEY parent_tconst (parent_tconst)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

    CREATE TABLE title_genre (
      title_id int unsigned NOT NULL,
      genre varchar(30) NOT NULL,
      KEY title_id (title_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

    CREATE TABLE title_principal (
      tconst char(10) NOT NULL,
      ordering tinyint unsigned NOT NULL,
      nconst char(10) NOT NULL,
      category varchar(100) NOT NULL,
      job varchar(100) DEFAULT NULL,
      characters varchar(100) DEFAULT NULL,
      PRIMARY KEY (tconst,ordering),
      KEY nconst (nconst)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

    CEATE TABLE title_rating (
      tconst char(10) NOT NULL,
      averageRating decimal(3,1) NOT NULL,
      numVotes int unsigned NOT NULL,
      PRIMARY KEY (tconst)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

    CREATE TABLE title_genre (
      title_id int unsigned NOT NULL,
      genre varchar(30) NOT NULL,
      PRIMARY KEY title_id (title_id,genre)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

## Example Dataset


```
 SELECT type, COUNT(*) AS cnt FROM title GROUP BY type ORDER BY 2 DESC;
```


## Data Format

Each dataset is contained in a gzipped, tab-separated-values (TSV) formatted file in the UTF-8 character set. The first line in each file contains headers that describe what is in each column. A ‘\N’ is used to denote that a particular field is missing or null for that title/name. The available datasets are as follows:

### title.akas.tsv.gz - Contains the following information for titles:

- titleId (string) - a tconst, an alphanumeric unique identifier of the title
- ordering (integer) – a number to uniquely identify rows for a given titleId
- title (string) – the localized title
- region (string) - the region for this version of the title
- language (string) - the language of the title
- types (array) - Enumerated set of attributes for this alternative title. One or more of the following: "alternative", "dvd", "festival", "tv", "video", "working", "original", "imdbDisplay". New values may be added in the future without warning
- attributes (array) - Additional terms to describe this alternative title, not enumerated
- isOriginalTitle (boolean) – 0: not original title; 1: original title

### title.basics.tsv.gz - Contains the following information for titles:
- tconst (string) - alphanumeric unique identifier of the title
- titleType (string) – the type/format of the title (e.g. movie, short, tvseries, tvepisode, video, etc)
- primaryTitle (string) – the more popular title / the title used by the filmmakers on promotional materials at the point of release
- originalTitle (string) - original title, in the original language
- isAdult (boolean) - 0: non-adult title; 1: adult title
- startYear (YYYY) – represents the release year of a title. In the case of TV Series, it is the series start year
- endYear (YYYY) – TV Series end year. ‘\N’ for all other title types
- runtimeMinutes – primary runtime of the title, in minutes
- genres (string array) – includes up to three genres associated with the title

### title.crew.tsv.gz – Contains the director and writer information for all the titles in IMDb. Fields include:
- tconst (string) - alphanumeric unique identifier of the title
- directors (array of nconsts) - director(s) of the given title
- writers (array of nconsts) – writer(s) of the given title

### title.episode.tsv.gz – Contains the tv episode information. Fields include:

- tconst (string) - alphanumeric identifier of episode
- parentTconst (string) - alphanumeric identifier of the parent TV Series
- seasonNumber (integer) – season number the episode belongs to
- episodeNumber (integer) – episode number of the tconst in the TV series

### title.principals.tsv.gz – Contains the principal cast/crew for titles
- tconst (string) - alphanumeric unique identifier of the title
- ordering (integer) – a number to uniquely identify rows for a given titleId
- nconst (string) - alphanumeric unique identifier of the name/person
- category (string) - the category of job that person was in
- job (string) - the specific job title if applicable, else '\N'
- characters (string) - the name of the character played if applicable, else '\N'

### title.ratings.tsv.gz – Contains the IMDb rating and votes information for titles

- tconst (string) - alphanumeric unique identifier of the title
- averageRating – weighted average of all the individual user ratings
- numVotes - number of votes the title has received

### name.basics.tsv.gz – Contains the following information for names:
- nconst (string) - alphanumeric unique identifier of the name/person
- primaryName (string)– name by which the person is most often credited
- birthYear – in YYYY format
- deathYear – in YYYY format if applicable, else '\N'
- primaryProfession (array of strings)– the top-3 professions of the person
- knownForTitles (array of tconsts) – titles the person is known for

Current as at [12/2022](https://www.imdb.com/interfaces/)


## Additional References
- https://github.com/dlwhittenbury/MySQL_IMDb_Project (discovered after)
