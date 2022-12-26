ALTER TABLE postcode ADD INDEX (country_code, postal_code);
ALTER TABLE postcode ADD INDEX (lat, lng);
