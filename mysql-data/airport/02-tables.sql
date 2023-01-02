\! echo "Creating airport tables"

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

SHOW TABLES;
