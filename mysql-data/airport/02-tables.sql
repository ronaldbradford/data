\! echo "Creating airport tables"

CREATE TABLE airport (
  airport_id    INT UNSIGNED NOT NULL, 
  ident         VARCHAR(7) NOT NULL,
  type          VARCHAR(20) NOT NULL,
  name          VARCHAR(100) NOT NULL,
  latitude      FLOAT NOT NULL,
  longitude     FLOAT NOT NULL,
  elevation_ft  SMALLINT NULL DEFAULT NULL,
  continent_code CHAR(2) NOT NULL,
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

CREATE TABLE airport_runway (
  runway_id     INT UNSIGNED NOT NULL,
  airport_id    INT UNSIGNED NOT NULL,
  airport_ident VARCHAR(7) NOT NULL,
  length_ft     SMALLINT NULL DEFAULT NULL,
  width_ft      SMALLINT NULL DEFAULT NULL,
  surface       VARCHAR(5) NOT NULL,
  lighted       BOOLEAN NOT NULL,
  closed        BOOLEAN NOT NULL,
  le_ident      VARCHAR(7) NOT NULL,
  le_latitude_deg  FLOAT NULL,
  le_longitude_deg FLOAT NULL,
  le_elevation_ft  SMALLINT NULL DEFAULT NULL,
  le_heading_deg_true SMALLINT NULL DEFAULT NULL,
  le_displaced_threshold_ft SMALLINT NULL DEFAULT NULL,
  he_ident      VARCHAR(7) NOT NULL,
  he_latitude_deg  FLOAT NULL,
  he_longitude_deg FLOAT NULL,
  he_elevation_ft  SMALLINT NULL DEFAULT NULL,
  he_heading_deg_true SMALLINT NULL DEFAULT NULL,
  he_displaced_threshold_ft SMALLINT NULL DEFAULT NULL,
  PRIMARY KEY(runway_id),
  KEY (airport_id)
);

CREATE TABLE navaid (
  navaid_id     INT UNSIGNED NOT NULL,
  filename      VARCHAR(100) NOT NULL,
  ident         VARCHAR(8) NOT NULL,
  name          VARCHAR(100) NOT NULL,
  type          VARCHAR(20) NOT NULL,
  frequency_mhz FLOAT NULL,
  latitude_deg  FLOAT NULL,
  longitude_deg FLOAT NULL,
  elevation_ft  SMALLINT NULL,
  country_id    CHAR(2) NOT NULL,
  dme_frequency_mhz FLOAT NULL,
  dme_channel       VARCHAR(10) NULL,
  dme_latitude_deg  FLOAT NULL,
  dme_longitude_deg FLOAT NULL,
  dme_elevation_ft  SMALLINT NULL DEFAULT NULL,
  slave_variation_deg FLOAT NULL,
  magnetic_variation_deg FLOAT NULL,
  usage_type    VARCHAR(10) NULL,
  power         VARCHAR(10) NULL,
  airport_ident VARCHAR(7) NULL,
  PRIMARY KEY(navaid_id),
  KEY (airport_ident)
);



SHOW TABLES;
