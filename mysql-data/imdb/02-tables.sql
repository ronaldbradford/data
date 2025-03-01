SELECT "Creating IMDb tables" AS msg;
SELECT "..name" AS msg;

CREATE TABLE name (
  name_id        INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
  nconst         CHAR(10) NOT NULL,
  name           VARCHAR(120) NOT NULL,
  born           SMALLINT NULL DEFAULT NULL,
  died           SMALLINT NULL DEFAULT NULL,
  professions    VARCHAR(80),
  known_for      VARCHAR(80),
  updated        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_name_nconst ON name(nconst);
CREATE INDEX idx_name_name ON name(name);

CREATE TABLE name_profession(
  name_id INT NOT NULL,
  profession VARCHAR(30) NOT NULL
);

CREATE UNIQUE INDEX idx_name_profession_pk ON name_profession (name_id, profession);
CREATE INDEX idx_name_profession_profession ON name_profession (profession);

CREATE table name_known_for (
  name_id  INT NOT NULL,
  title_id INT NOT NULL
);

CREATE UNIQUE INDEX idx_known_for ON name_known_for (name_id, title_id);
CREATE INDEX idx_known_for_title_id ON name_known_for (title_id);

CREATE TABLE title (
  title_id       INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
  tconst         CHAR(10) NOT NULL,
  type           VARCHAR(12) NOT NULL,
  title          VARCHAR(600) NOT NULL,
  original_title VARCHAR(600) NOT NULL,
  is_adult       BOOLEAN NOT NULL,
  start_year     SMALLINT NULL DEFAULT NULL,
  end_year       SMALLINT NULL DEFAULT NULL,
  run_time_mins  SMALLINT DEFAULT NULL,
  genres         VARCHAR(32),
  updated        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_title_tconst ON title(tconst);
CREATE INDEX idx_title_title ON title(title);

CREATE TABLE title_genre(
  title_id INT NOT NULL,
  genre VARCHAR(20) NOT NULL
);

CREATE UNIQUE INDEX idx_title_genre_pk ON title_genre(title_id, genre);
CREATE INDEX idx_title_genre_genre ON title_genre(genre);

CREATE TABLE tmp_title_episode(
  tconst         CHAR(10) NOT NULL,
  parent_tconst  CHAR(10) NOT NULL,
  season         INT NULL DEFAULT NULL,
  episode        INT NULL DEFAULT NULL,
  PRIMARY KEY (tconst, parent_tconst),
  INDEX (parent_tconst)
);

CREATE TABLE title_episode(
  parent_title_id CHAR(10) NOT NULL,
  title_id        CHAR(10) NOT NULL,
  season          INT NULL DEFAULT NULL,
  episode         INT NULL DEFAULT NULL
);

CREATE UNIQUE INDEX idx_title_eposide_pk ON title_episode(parent_title_id, title_id);
CREATE INDEX idx_title_eposide_title_id ON title_episode(title_id);

CREATE TABLE tmp_title_rating(
  tconst         CHAR(10) NOT NULL PRIMARY KEY,
  average_rating DECIMAL(3,1) NOT NULL,
  num_votes      INT NOT NULL
);

CREATE TABLE title_rating(
  title_id INT NOT NULL PRIMARY KEY,
  average_rating DECIMAL(3,1) NOT NULL,
  num_votes      INT NOT NULL
);

CREATE TABLE tmp_title_principal(
  tconst         CHAR(10) NOT NULL,
  ordering       TINYINT NOT NULL,
  nconst         CHAR(10) NOT NULL,
  category       VARCHAR(20) NOT NULL,
  job            VARCHAR(500) NULL,
  characters     TEXT NULL,
  PRIMARY KEY (tconst, ordering),
  INDEX (nconst)
);

CREATE TABLE title_principal(
  title_id       INT NOT NULL,
  name_id        INT NOT NULL,
  ordering       TINYINT NOT NULL,
  category       VARCHAR(20) NOT NULL,
  job            VARCHAR(500) NULL,
  characters     TEXT NULL
);

ALTER TABLE title_principal ADD PRIMARY KEY(title_id, name_id, ordering);
CREATE INDEX idx_title_principal_name_id ON title_principal(name_id);

CREATE TABLE title_name_character(
  tnc_id         INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
  title_id       INT NOT NULL,
  name_id        INT NOT NULL,
  character_name VARCHAR(500));

CREATE INDEX idx_title_name_character_title_id ON title_name_character(title_id);
CREATE INDEX idx_title_name_character_name_id ON title_name_character(name_id);
CREATE INDEX idx_title_name_character_character_name ON title_name_character(character_name(25));

CREATE TABLE credit(
  name    VARCHAR(20) NOT NULL PRIMARY KEY,
  cnt     INT NOT NULL
);

CREATE TABLE genre(
  genre   VARCHAR(20) NOT NULL PRIMARY KEY,
  cnt     INT NOT NULL
);

SHOW TABLES;
