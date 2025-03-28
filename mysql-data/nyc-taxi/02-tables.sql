CREATE TABLE yellow_taxi(
id      INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
trip_id INT UNSIGNED NOT NULL,
VendorID INT UNSIGNED NOT NULL, 
tpep_pickup_datetime DATETIME NOT NULL, 
tpep_dropoff_datetime DATETIME NOT NULL,
passenger_count DECIMAL(4,1) NULL DEFAULT NULL,
trip_distance DECIMAL(7,2) NOT NULL, 
RatecodeID TINYINT UNSIGNED NOT NULL, 
store_and_fwd_flag CHAR(1) NOT NULL,
PULocationID INT UNSIGNED NOT NULL,
DOLocationID INT UNSIGNED NOT NULL,
payment_type TINYINT UNSIGNED NOT NULL, 
fare_amount DECIMAL(7,2) NOT NULL,
extra DECIMAL(7,2) NOT NULL,
mta_tax DECIMAL(7,2) NOT NULL, 
tip_amount DECIMAL(7,2) NOT NULL, 
tolls_amount DECIMAL(7,2) NOT NULL, 
improvement_surcharge DECIMAL(7,2) NOT NULL,
total_amount DECIMAL(7,2) NOT NULL, 
congestion_surcharge DECIMAL(7,2) NOT NULL, 
airport_fee DECIMAL(7,2) NOT NULL,
INDEX (tpep_pickup_datetime),
INDEX (PULocationID)
);

SHOW TABLES;
