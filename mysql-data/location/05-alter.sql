\! echo "Altering schema for optimal use"
ALTER TABLE place ADD COLUMN display_name VARCHAR(500) 
  GENERATED ALWAYS AS (JSON_UNQUOTE(name->"$.display_name"));
ALTER TABLE place 
  ADD INDEX (display_name),
  ADD INDEX (country_code);
