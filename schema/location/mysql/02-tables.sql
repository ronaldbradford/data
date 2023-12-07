\! echo "Creating location tables"

\! echo "..continent"
CREATE TABLE continent(
  continent_id  CHAR(2) NOT NULL,
  name          VARCHAR(20) NOT NULL,
  PRIMARY KEY (continent_id)
);

\! echo "..country Based of ISO-3166"
CREATE TABLE country (
  country_id       CHAR(2) NOT NULL COMMENT 'ISO2',
  name             VARCHAR(100) NOT NULL,
  continent_id     CHAR(2) NOT NULL,
  iso_official     BOOLEAN NOT NULL DEFAULT 1,
  iso3             CHAR(3) NULL,
  wikipedia_url    VARCHAR(100) NOT NULL,
  capital          VARCHAR(60) NULL,
  region           VARCHAR(20) NULL,
  sub_region       VARCHAR(50) NULL,
  PRIMARY KEY (country_id),
  KEY (name)
);

\! echo "..country_subdivision (ISO-3166-2)"
CREATE TABLE country_subdivision (
  subdivision_id   CHAR(6) NOT NULL,
  country_id       CHAR(2) NOT NULL,
  name             VARCHAR(100) NOT NULL,
  PRIMARY KEY (subdivision_id),
  INDEX (country_id)
);

\! echo "..country_state"
CREATE TABLE country_state (
  country_id       CHAR(2) NOT NULL COMMENT 'ISO2',
  state_id         VARCHAR(3) NOT NULL,
  name             VARCHAR(100) NOT NULL,
  capital          VARCHAR(100) NULL,
  PRIMARY KEY(country_id, state_id)
);

SHOW TABLES;
