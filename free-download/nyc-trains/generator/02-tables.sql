\! echo "Creating nyc_trains tables"

-- MySQL's docker-entrypoint-initdb.d runs each *.sql file as its own
-- separate `mysql` client invocation, so 01-schema.sql's `USE nyc_trains;`
-- doesn't carry over to this file's connection — select it again here.
-- (Running both via `mysql < 01-schema.sql; mysql ... < 02-tables.sql`
-- outside Docker needs this same explicit USE for the same reason.)
USE nyc_trains;

\! echo "..nyc_trains"
CREATE TABLE nyc_trains (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  generated_at  DATETIME(6) NOT NULL COMMENT 'UTC snapshot time (FeatureCollection.generated_at)',
  line          VARCHAR(20) NOT NULL COMMENT 'feed id, e.g. 1234567S, ACE, LIRR, MNR, PATH',
  train_count   INT UNSIGNED NOT NULL COMMENT 'features[] length in position',
  position      JSON NOT NULL COMMENT 'GeoJSON FeatureCollection for this line at generated_at',
  PRIMARY KEY (id),
  KEY (line, generated_at)
);

SHOW TABLES;
