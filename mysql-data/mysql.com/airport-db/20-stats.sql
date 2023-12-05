# Queries that produce aggregated statistics. Ideal for admin dashboards

\! echo "Types of Planes"
SELECT     t.identifier, COUNT(*) AS planes
FROM       airplane a
INNER JOIN airplane_type t USING (type_id)
GROUP BY   identifier;

\! echo "Airports per country"
SELECT     g.country, COUNT(*) as airports
FROM       airport a
INNER JOIN airport_geo g USING (airport_id)
GROUP BY   country
ORDER BY   2 DESC;

\! echo "Top 20 Airlines with most flights per year"
SELECT     a.airlinename, YEAR(f.departure) AS yr, COUNT(*) AS flights
FROM       flight f
INNER JOIN airline a USING (airline_id)
GROUP BY   a.airline_id, YEAR(f.departure)
ORDER BY 3 DESC
LIMIT 20;

\! echo "Top 25 Australian passengers in Jun 2015"
SELECT     b.passenger_id, p.firstname, p.lastname, COUNT(*) AS trips, MIN(b.price) AS min_price, AVG(b.price) AS avg_price, MAX(b.price) AS max_price
FROM       booking b
INNER JOIN passengerdetails pd USING (passenger_id)
INNER JOIN passenger p USING (passenger_id)
INNER JOIN flight f USING (flight_id)
WHERE      pd.country = 'AUSTRALIA'
AND        f.departure BETWEEN '2015-06-01' AND '2015-06-30'
GROUP BY   b.passenger_id, p.firstname, p.lastname
ORDER BY 4 DESC
LIMIT 25;

\! echo "Flights per day"
SELECT DATE(departure) AS date, count(*) FROM flight GROUP BY date(departure) ORDER BY 1;

\! echo "Single Booking Lookup"
SELECT * FROM booking WHERE flight_id=758655;
SELECT * FROM flight WHERE flight_id=758655;
SELECT * FROM airport WHERE airport_id IN (4167, 8033);
SELECT * FROM airport_geo WHERE airport_id in (4167, 8033);
SELECT * FROM airline WHERE airline_id=113;
SELECT * FROM airplane WHERE airplane_id=3296;
SELECT * FROM airplane_type WHERE type_id=232;
SELECT * FROM passenger WHERE passenger_id=22514;
SELECT * FROM flight_log WHERE flight_id=758655;
SELECT * FROM flightschedule WHERE flightno='ZI8976';
