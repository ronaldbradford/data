\! echo "Loading names for airports"
LOAD DATA 
  LOCAL INFILE 'airports.csv'
  INTO TABLE airport 
  COLUMNS TERMINATED BY ',' 
          OPTIONALLY ENCLOSED BY '"'
  IGNORE 1 LINES
  (airport_id,ident,type,name,latitude,longitude,@elevation_ft,continent_code,country_code,region_code,municipality,@scheduled_service,gps_code,iata_code,local_code,home_url,wikipedia_url,keywords)
  SET elevation_ft = IF(@elevation_ft='',NULL,@elevation_ft),
      scheduled_service = IF(@scheduled_service='yes',TRUE,FALSE);

LOAD DATA 
  LOCAL INFILE 'countries.csv'
  INTO TABLE country 
  COLUMNS TERMINATED BY ',' 
          OPTIONALLY ENCLOSED BY '"'
  IGNORE 1 LINES
  (country_id, country_code, name, continent_code, wikipedia_url, keywords);

LOAD DATA 
  LOCAL INFILE 'regions.csv'
  INTO TABLE region 
  COLUMNS TERMINATED BY ',' 
          OPTIONALLY ENCLOSED BY '"'
  IGNORE 1 LINES
  (region_id, region_code, local_code, name, continent_code, country_code, wikipedia_url, keywords);

LOAD DATA
  LOCAL INFILE 'airport-frequencies.csv'
  INTO TABLE airport_frequency
  COLUMNS TERMINATED BY ','
          OPTIONALLY ENCLOSED BY '"'
  IGNORE 1 LINES
  (frequency_id, airport_id, ident, type, description, frequency_mhz);

LOAD DATA
  LOCAL INFILE 'runways.csv'
  INTO TABLE airport_runway
  COLUMNS TERMINATED BY ','
          OPTIONALLY ENCLOSED BY '"'
  IGNORE 1 LINES
  (runway_id, airport_id, airport_ident, @length_ft, @width_ft, surface, lighted, closed, le_ident, @le_latitude_deg, @le_longitude_deg, @le_elevation_ft, @le_heading_deg_true, @le_displaced_threshold_ft, he_ident, @he_latitude_deg, @he_longitude_deg, @he_elevation_ft, @he_heading_deg_true, @he_displaced_threshold_ft)
  SET length_ft = IF(@length_ft='',NULL,@length_ft),
      width_ft = IF(@width_ft='',NULL,@width_ft),
      le_elevation_ft = IF(@le_elevation_ft='',NULL,@le_elevation_ft),
      le_latitude_deg = IF(@le_latitude_deg='',NULL,@le_latitude_deg),
      le_longitude_deg = IF(@le_longitude_deg='',NULL,@le_longitude_deg),
      le_heading_deg_true = IF(@le_heading_deg_true='',NULL,@le_heading_deg_true),
      he_elevation_ft = IF(@he_elevation_ft='',NULL,@he_elevation_ft),
      he_latitude_deg = IF(@he_latitude_deg='',NULL,@he_latitude_deg),
      he_heading_deg_true = IF(@he_heading_deg_true='',NULL,@he_heading_deg_true),
      he_longitude_deg = IF(@he_longitude_deg='',NULL,@he_longitude_deg),
      le_displaced_threshold_ft= IF(@le_displaced_threshold_ft='',NULL,@le_displaced_threshold_ft),
      he_displaced_threshold_ft= IF(@he_displaced_threshold_ft='',NULL,@he_displaced_threshold_ft);

LOAD DATA
  LOCAL INFILE 'navaids.csv'
  INTO TABLE navaid
  COLUMNS TERMINATED BY ','
          OPTIONALLY ENCLOSED BY '"'
  IGNORE 1 LINES
(navaid_id, filename, ident, name, type, @frequency_mhz, latitude_deg, longitude_deg, @elevation_ft, country_id, @dme_frequency_mhz, @dme_channel, @dme_latitude_deg, @dme_longitude_deg, @dme_elevation_ft, @slave_variation_deg, @magnetic_variation_deg, @usage_type, @power, @airport_ident)
  SET elevation_ft = IF(@elevation_ft='',NULL,@elevation_ft),
      dme_channel = IF(@dme_channel='',NULL,@dme_channel),
      frequency_mhz = IF(@frequency_mhz='',NULL,@frequency_mhz),
      dme_frequency_mhz = IF(@dme_frequency_mhz='',NULL,@dme_frequency_mhz),
      dme_elevation_ft = IF(@dme_elevation_ft='',NULL,@dme_elevation_ft),
      dme_latitude_deg = IF(@dme_latitude_deg='',NULL,@dme_latitude_deg),
      dme_longitude_deg = IF(@dme_longitude_deg='',NULL,@he_longitude_deg),
      slave_variation_deg = IF(@slave_variation_deg='',NULL,@slave_variation_deg),
      magnetic_variation_deg = IF(@magnetic_variation_deg='',NULL,@magnetic_variation_deg),
      power = IF(@power='',NULL,@power),
      usage_type = IF(@usage_type='',NULL,@usage_type),
      airport_ident = IF(@airport_ident='',NULL,@airport_ident);
UPDATE navaid m,
       airport a
SET    m.airport_id = a.airport_id
WHERE  m.airport_ident = a.ident;
