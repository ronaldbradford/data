CREATE OR REPLACE TABLE geonames (
      geonameid          BIGINT,
      name               VARCHAR,
      asciiname          VARCHAR,
      alternatenames     VARCHAR,
      latitude           DOUBLE,
      longitude          DOUBLE,
      feature_class      VARCHAR,
      feature_code       VARCHAR,
      country_code       VARCHAR,
      cc2                VARCHAR,
      admin1_code        VARCHAR,
      admin2_code        VARCHAR,
      admin3_code        VARCHAR,
      admin4_code        VARCHAR,
      population         BIGINT,
      elevation          INTEGER,
      dem                INTEGER,
      timezone           VARCHAR,
      modification_date  DATE
);
COPY geonames FROM 'allCountries.txt.gz' (
      FORMAT csv, DELIMITER '\t', HEADER true,
      QUOTE '', ESCAPE '', NULLSTR '', COMPRESSION gzip
);

CREATE INDEX ix_geonames_country ON geonames (country_code);
CREATE INDEX ix_geonames_name ON geonames (name);
