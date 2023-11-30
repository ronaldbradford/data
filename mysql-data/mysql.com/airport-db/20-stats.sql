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
