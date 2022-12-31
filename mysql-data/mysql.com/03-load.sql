# TABLE_ORDER="airport airline airplane_type airplane airport_geo airport_reachable weatherdata employee flightschedule flight flight_log passenger passengerdetails booking"

\! echo "Loading Airports"
LOAD DATA LOCAL INFILE 'airportdb@airport@@0.tsv' INTO TABLE airport FIELDS TERMINATED BY '\t';
\! echo "Loading Airlines"
LOAD DATA LOCAL INFILE 'airline.tsv' INTO TABLE airline FIELDS TERMINATED BY '\t';
\! echo "Loading Airplane Types"
LOAD DATA LOCAL INFILE 'airportdb@airplane_type@@0.tsv' INTO TABLE airplane_type FIELDS TERMINATED BY '\t';
\! echo "Loading Airplanes"
LOAD DATA LOCAL INFILE 'airportdb@airplane@@0.tsv' INTO TABLE airplane FIELDS TERMINATED BY '\t';


\! echo "Patching Airport Geo Locations"
ALTER TABLE airport_geo DROP INDEX geolocation_spt;
ALTER TABLE airport_geo MODIFY geolocation POINT NOT NULL SRID 0; 
ALTER TABLE airport_geo ADD SPATIAL KEY `geolocation_spt` (`geolocation`);
\! echo "Loading Airport Geo Locations"
LOAD DATA LOCAL INFILE 'airportdb@airport_geo@@0.tsv' INTO TABLE airport_geo FIELDS TERMINATED BY '\t' (airport_id, name, city, country, latitude, longitude, @point) SET geolocation = ST_SRID(POINT(latitude,longitude), 0);

\! echo "Loading Airport Reachable "
LOAD DATA LOCAL INFILE 'airportdb@airport_reachable.tsv' INTO TABLE airport_reachable FIELDS TERMINATED BY '\t';
\! echo "Loading Weather Data"
LOAD DATA LOCAL INFILE 'airportdb@weatherdata@0.tsv' INTO TABLE weatherdata FIELDS TERMINATED BY '\t';
LOAD DATA LOCAL INFILE 'airportdb@weatherdata@@1.tsv' INTO TABLE weatherdata FIELDS TERMINATED BY '\t';
\! echo "Loading Employee data"
LOAD DATA LOCAL INFILE 'airportdb@employee@@0.tsv' INTO TABLE employee FIELDS TERMINATED BY '\t';
\! echo "Loading Flight Schedules"
LOAD DATA LOCAL INFILE 'airportdb@flightschedule@@0.tsv' INTO TABLE flightschedule FIELDS TERMINATED BY '\t';
\! echo "Loading Flights"
LOAD DATA LOCAL INFILE 'airportdb@flight@@0.tsv' INTO TABLE flight FIELDS TERMINATED BY '\t';
\! echo "Loading Flight Logs"
LOAD DATA LOCAL INFILE 'airportdb@flight_log.tsv' INTO TABLE flight_log FIELDS TERMINATED BY '\t';
\! echo "Loading Passengers"
LOAD DATA LOCAL INFILE 'airportdb@passenger@@0.tsv' INTO TABLE passenger FIELDS TERMINATED BY '\t';
\! echo "Loading Passenger Details"
LOAD DATA LOCAL INFILE 'airportdb@passengerdetails@@0.tsv' INTO TABLE passengerdetails FIELDS TERMINATED BY '\t';
\! echo "Loading Bookings (last and largest table)"
LOAD DATA LOCAL INFILE 'booking.tsv' INTO TABLE booking FIELDS TERMINATED BY '\t';
