\! echo "Creating Tables"
CREATE TABLE place (
  place_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name JSON NULL,
  country_code CHAR(2) NULL
);
