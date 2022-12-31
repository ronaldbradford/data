\! echo "Loading data into tables"
LOAD DATA 
  LOCAL INFILE 'allCountries.tsv' 
  INTO TABLE postcode 
  FIELDS TERMINATED BY '\t'
  IGNORE 0 LINES
  (country_code, postal_code, place_name, 
   admin_name1, admin_code1,
   admin_name2, admin_code2,
   admin_name3, admin_code3,
   lat, lng, @accuracy)
   SET accuracy = IF(@accuracy = '',NULL,@accuracy);

SELECT NOW() AS now, COUNT(*) AS cnt FROM postcode;
SELECT * FROM postcode LIMIT 10;
