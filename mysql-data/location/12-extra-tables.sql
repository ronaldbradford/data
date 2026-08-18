\! echo "Creating Extract Tables"
DROP TABLE IF EXISTS country;
CREATE TABLE country (
  country_code CHAR(2) NOT NULL PRIMARY KEY,
  name VARCHAR(50) NOT NULL
);

INSERT INTO country (country_code, name)
SELECT DISTINCT  UPPER(name->>'$.address.country_code') AS country_code,
                 name->>'$.address.country'      AS country
FROM place
WHERE name->>'$.address.country' IS NOT NULL;

DROP TABLE IF EXISTS city;

CREATE TABLE city (
  name VARCHAR(100) COLLATE utf8mb4_0900_as_cs NOT NULL,
  country_code CHAR(2) NOT NULL,
  PRIMARY KEY (country_code, name)
);

INSERT INTO city (name, country_code)
SELECT DISTINCT  name->>'$.address.city'      AS name,        
                 UPPER(name->>'$.address.country_code') AS country_code
FROM place
WHERE name->>'$.address.city' IS NOT NULL;


SELECT COUNT(*) AS countries from country;
SELECT COUNT(*) AS cities from city;
