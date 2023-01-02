\! echo "Creating Tables"
CREATE TABLE postcode (
  postcode_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  country_code  CHAR(2) NOT NULL,
  postal_code   VARCHAR(20) NOT NULL,
  place_name    VARCHAR(180) NOT NULL,
  admin_name1  VARCHAR(100) NULL,
  admin_code1  VARCHAR(20) NULL,
  admin_name2  VARCHAR(100) NULL,
  admin_code2  VARCHAR(20) NULL,
  admin_name3  VARCHAR(100) NULL,
  admin_code3  VARCHAR(20) NULL,
  lat        FLOAT NOT NULL,
  lng        FLOAT NOT NULL,
  accuracy   TINYINT UNSIGNED NULL
);


CREATE TABLE postcode_geo (
  postcode_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  country_code  CHAR(2) NOT NULL,
  postal_code   VARCHAR(20) NOT NULL,
  location      POINT NOT NULL SRID 0,
SPATIAL INDEX (location)
);
  

SHOW TABLES;
