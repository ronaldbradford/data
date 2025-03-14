LOAD DATA 
  LOCAL INFILE 'yellow_tripdata_2022-01.tsv'
  INTO TABLE yellow_taxi
  FIELDS TERMINATED BY '\t'
  IGNORE 1 LINES
  (trip_id,VendorID,tpep_pickup_datetime,tpep_dropoff_datetime,passenger_count,trip_distance,RatecodeID,store_and_fwd_flag,PULocationID,DOLocationID,payment_type,fare_amount,extra,mta_tax,tip_amount,tolls_amount,improvement_surcharge,total_amount,congestion_surcharge,airport_fee);

SELECT NOW() AS now, COUNT(*) AS cnt FROM yellow_taxi;
SELECT * FROM yellow_taxi LIMIT 10;
