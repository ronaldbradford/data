select DAY(tpep_pickup_datetime),COUNT(*) from yellow_taxi GROUP BY DAY(tpep_pickup_datetime);

-- Total number of trips
SELECT COUNT(*) AS total_trips FROM yellow_taxi;

-- Average trip distance and fare amount
SELECT
    AVG(trip_distance) AS avg_trip_distance,
    AVG(fare_amount) AS avg_fare_amount
FROM yellow_taxi;

-- Total revenue breakdown by payment type
SELECT
    payment_type,
    COUNT(*) AS total_trips,
    SUM(total_amount) AS total_revenue
FROM yellow_taxi
GROUP BY payment_type;

-- Peak pickup times (hourly distribution)
SELECT
    HOUR(tpep_pickup_datetime) AS pickup_hour,
    COUNT(*) AS trip_count
FROM yellow_taxi
GROUP BY pickup_hour
ORDER BY trip_count DESC;

-- Top 10 busiest pickup locations
SELECT
    PULocationID,
    COUNT(*) AS total_pickups
FROM yellow_taxi
GROUP BY PULocationID
ORDER BY total_pickups DESC
LIMIT 10;

-- Top 10 busiest dropoff locations
SELECT
    DOLocationID,
    COUNT(*) AS total_dropoffs
FROM yellow_taxi
GROUP BY DOLocationID
ORDER BY total_dropoffs DESC
LIMIT 10;

-- Distribution of passenger count
SELECT
    passenger_count,
    COUNT(*) AS trip_count
FROM yellow_taxi
GROUP BY passenger_count
ORDER BY trip_count DESC;

-- Percentage of trips where tips were given
SELECT
    COUNT(CASE WHEN tip_amount > 0 THEN 1 END) / COUNT(*) * 100 AS tip_percentage
FROM yellow_taxi;

-- Most frequent trip routes (pickup and dropoff location pairs)
SELECT
    PULocationID,
    DOLocationID,
    COUNT(*) AS trip_count
FROM yellow_taxi
GROUP BY PULocationID, DOLocationID
ORDER BY trip_count DESC
LIMIT 10;

-- Revenue impact of congestion surcharge
SELECT
    congestion_surcharge,
    COUNT(*) AS num_trips,
    SUM(total_amount) AS total_revenue
FROM yellow_taxi
GROUP BY congestion_surcharge
ORDER BY congestion_surcharge DESC;

-- Trips with airport fees (to analyze airport traffic)
SELECT
    COUNT(*) AS airport_trips,
    SUM(airport_fee) AS total_airport_fees
FROM yellow_taxi
WHERE airport_fee > 0;
