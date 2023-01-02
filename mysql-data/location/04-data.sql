\! echo "Adding additional initial data"
UPDATE place
SET    country_code=UPPER(JSON_UNQUOTE(name->"$.address.country_code"));
