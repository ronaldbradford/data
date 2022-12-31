\! echo "Adding additional initial data"
INSERT INTO postcode_geo(postcode_id, country_code, postal_code, location)
SELECT postcode_id, country_code, postal_code, POINT(lat, lng) FROM postcode;

