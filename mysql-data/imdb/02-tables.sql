\! echo "Creating IMDb tables"
CREATE TABLE name (
  name_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nconst        CHAR(10) NOT NULL,
  name          VARCHAR(120) NOT NULL,
  birth_year    SMALLINT UNSIGNED NULL DEFAULT NULL,
  death_year    SMALLINT UNSIGNED NULL DEFAULT NULL,
  profession    VARCHAR(64), # surprising these max out at 64.
  known_for     VARCHAR(64), # 64, has null 12/22
  PRIMARY KEY (name_id),
  UNIQUE KEY (nconst)
);

CREATE TABLE title (
  title_id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
  tconst        CHAR(10) NOT NULL,
  type          VARCHAR(12) NOT NULL,
  title         VARCHAR(600) NOT NULL,
  original_title VARCHAR(600) NOT NULL,
  is_adult      BOOLEAN NOT NULL,
  start_year    SMALLINT UNSIGNED NULL DEFAULT NULL,
  end_year      SMALLINT UNSIGNED NULL DEFAULT NULL,
  run_time_mins SMALLINT UNSIGNED DEFAULT NULL,
  genres        VARCHAR(32),
  PRIMARY KEY (title_id),
  UNIQUE KEY (tconst)
);

CREATE TABLE title_episode(
  tconst        CHAR(10) NOT NULL,
  parent_tconst CHAR(10) NOT NULL,
  season        SMALLINT UNSIGNED NULL DEFAULT NULL,
  episode       SMALLINT UNSIGNED NULL DEFAULT NULL,
  PRIMARY KEY (tconst, parent_tconst),
  INDEX (parent_tconst)
);

#select max(length(directors)), max(length(writers)) from title_crew;
#+------------------------+----------------------+
#| max(length(directors)) | max(length(writers)) |
#+------------------------+----------------------+
#|                   4987 |                13414 |
#+------------------------+----------------------+
CREATE TABLE title_crew(
  crew_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
  tconst        CHAR(10) NOT NULL,
  directors     TEXT NULL,
  writers       TEXT NULL,
  PRIMARY KEY (crew_id),
  INDEX (tconst)
);

CREATE TABLE title_rating(
  tconst        CHAR(10) NOT NULL,
  averageRating DECIMAL(3,1) NOT NULL,
  numVotes      INT UNSIGNED NOT NULL,
  PRIMARY KEY (tconst)
);

CREATE TABLE title_principal(
  tconst        CHAR(10) NOT NULL,
  ordering      TINYINT UNSIGNED NOT NULL,
  nconst        CHAR(10) NOT NULL,
  category      VARCHAR(20) NOT NULL,
  job           VARCHAR(500) NULL,
  characters    TEXT NULL,
  PRIMARY KEY (tconst, ordering),
  INDEX (nconst)
);

SHOW TABLES;
