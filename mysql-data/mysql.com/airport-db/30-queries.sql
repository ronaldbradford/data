\! echo "IATA Airports in Canada"
SELECT     a.iata, a.name, g.city
FROM       airport a
INNER JOIN airport_geo g USING (airport_id)
WHERE      g.country = 'CANADA'
AND        a.iata IS NOT NULL
ORDER BY   2;

\! echo "Count of Bookings starting at \$500"
SELECT   booking.price, COUNT(*)
FROM     booking
WHERE    booking.price > 500
GROUP BY booking.price
ORDER BY booking.price
LIMIT 10;


\! echo "Average age of passengers in 3 countries per airline"
SELECT     airline.airlinename,
           ROUND(AVG(datediff(departure,birthdate)/365.25),1) AS avg_age,
           COUNT(*) AS passengers
FROM       booking
INNER JOIN flight USING (flight_id)
INNER JOIN airline USING (airline_id)
INNER JOIN passengerdetails USING (passenger_id)
WHERE      country IN ("SWITZERLAND", "FRANCE", "ITALY")
GROUP BY   airline.airlinename
ORDER BY   airline.airlinename, avg_age
LIMIT 10;


\! echo "Ticket count and total sales per airline in US"
SELECT     airline.airlinename,
           SUM(booking.price) AS total_sales,
           COUNT(*) AS tickets
FROM       booking
INNER JOIN flight USING (flight_id)
INNER JOIN airline USING (airline_id)
INNER JOIN airport_geo ON flight.from = airport_geo.airport_id
WHERE      airport_geo.country = "UNITED STATES"
GROUP BY   airline.airlinename
ORDER BY   tickets DESC, airline.airlinename
LIMIT 10;
