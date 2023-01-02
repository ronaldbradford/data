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

