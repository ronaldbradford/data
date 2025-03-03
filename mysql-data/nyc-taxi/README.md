# NYC Yellow Taxi Trips

This data from [NYC Open Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) is a citywide platform where all agencies share data for free, with everyone, to
increase transparency and foster civic innovation.

## Data Summary

There are monthly data files for 4 different types of fares.  This example only uses Yellow Taxi trips.
Data is now available after 2 months. Data starts in 2009.


- Month: 2022-01
- Rows: 246,3931
- Reasonable amount of bad data
- 2022-01-21 was the busyist day, it was a Friday.
- Monday's are the busyist weekday!!!

## Pre-requisites
- Python 3
- Needed libraries installed with

```
   pip3 install -r requirements.txt
```

## Get source data

    MONTH=2022-01
    wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_${MONTH}.parquet
    wget https://d37ci6vzurychx.cloudfront.net/misc/taxi+_zone_lookup.csv
    dos2unix taxi+_zone_lookup.csv
    ./convert.py yellow_tripdata_${MONTH}.parquet
    wc -l yellow_tripdata_${MONTH}.tsv
    head yellow_tripdata_${MONTH}.tsv

    # Local server
    mysql < install.sql
    pigz yellow_tripdata_${MONTH}.tsv

    # For docker usage
    docker cp yellow_tripdata_${MONTH}.tsv $DB_CONTAINER:.

NOTE: There is no way to stream a file into MySQL `INFILE` or `mysqlimport` command.

## Data Format

For the 2022-01 data from [Yellow Trips Data Dictionary](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf)
- VendorID A code indicating the TPEP provider that provided the record. (1= Creative Mobile Technologies, LLC; 2= VeriFone Inc.)
- tpep_pickup_datetime The date and time when the meter was engaged.
- tpep_dropoff_datetime The date and time when the meter was disengaged.
- Passenger_count The number of passengers in the vehicle. This is a driver-entered value.
- Trip_distance The elapsed trip distance in miles reported by the taximeter.
- PULocationID TLC Taxi Zone in which the taximeter was engaged
- DOLocationID TLC Taxi Zone in which the taximeter was disengaged
- RateCodeID The final rate code in effect at the end of the trip.(1= Standard rate,2=JFK,3=Newark,4=Nassau or Westchester,5=Negotiated fare,6=Group ride)
- Store_and_fwd_flag This flag indicates whether the trip record was held in vehicle memory before sending to the vendor, aka “store and forward,” because the vehicle did not have a connection to the server. (Y= store and forward trip, N= not a store and forward trip)
- Payment_type A numeric code signifying how the passenger paid for the trip. (1= Credit card,2= Cash,3= No charge,4= Dispute,5= Unknown,6= Voided trip)
- Fare_amount The time-and-distance fare calculated by the meter.
-Extra Miscellaneous extras and surcharges. Currently, this only includes the $0.50 and $1 rush hour and overnight charges.
- MTA_tax $0.50 MTA tax that is automatically triggered based on the meteredrate in use.
- Improvement_surcharge $0.30 improvement surcharge assessed trips at the flag drop. The improvement surcharge began being levied in 2015.
- Tip_amount Tip amount – This field is automatically populated for credit card
tips. Cash tips are not included.
- Tolls_amount Total amount of all tolls paid in trip.
- Total_amount The total amount charged to passengers. Does not include cash tips.
- Congestion_Surcharge Total amount collected in trip for NYS congestion surcharge.
-Airport_fee $1.25 for pick up only at LaGuardia and John F. Kennedy Airports

## Define your Database Connectivity

- See [../DOCKER.md](../DOCKER.md) for a standalone local environment. The following instructions will use
this setup, however it can be easily configured for any local or cloud-based MySQL instance.

## Load Data into MySQL

    docker cp allCountries.tsv ${DB_CONTAINER}:/
    SCHEMA="nyc_taxi"

    docker exec -i ${DB_CONTAINER}  mysql -u${DBA_USER} -p${DBA_PASSWD} --local-infile --show-warnings < 01-schema.sql
    docker exec -i ${DB_CONTAINER}  mysql -u${DBA_USER} -p${DBA_PASSWD} --local-infile --show-warnings ${SCHEMA} < 02-tables.sql
    docker exec -i ${DB_CONTAINER}  mysql -u${DBA_USER} -p${DBA_PASSWD} --local-infile --show-warnings ${SCHEMA} < 03-load.sql

## Tables

- yellow_tripdata_2022-01

```
CREATE TABLE `yellow_tripdata_2022_01` (
  `trip_id` int unsigned NOT NULL,
  `VendorID` int unsigned NOT NULL,
  `tpep_pickup_datetime` datetime NOT NULL,
  `tpep_dropoff_datetime` datetime NOT NULL,
  `passenger_count` decimal(4,1) DEFAULT NULL,
  `trip_distance` decimal(7,2) NOT NULL,
  `RatecodeID` tinyint unsigned NOT NULL,
  `store_and_fwd_flag` char(1) NOT NULL,
  `PULocationID` int unsigned NOT NULL,
  `DOLocationID` int unsigned NOT NULL,
  `payment_type` tinyint unsigned NOT NULL,
  `fare_amount` decimal(7,2) NOT NULL,
  `extra` decimal(7,2) NOT NULL,
  `mta_tax` decimal(7,2) NOT NULL,
  `tip_amount` decimal(7,2) NOT NULL,
  `tolls_amount` decimal(7,2) NOT NULL,
  `improvement_surcharge` decimal(7,2) NOT NULL,
  `total_amount` decimal(7,2) NOT NULL,
  `congestion_surcharge` decimal(7,2) NOT NULL,
  `airport_fee` decimal(7,2) NOT NULL,
  PRIMARY KEY (`trip_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

## Example Dataset

    mysql> select min(tpep_pickup_datetime), max(tpep_pickup_datetime), max(passenger_count), max(trip_distance), max(fare_amount), max(extra) from yellow_tripdata_2022_01 where trip_distance < 10000 and fare_amount < 10000\G
    *************************** 1. row ***************************
    min(tpep_pickup_datetime): 2008-12-31 22:23:09
    max(tpep_pickup_datetime): 2022-05-18 20:41:57
         max(passenger_count): 9.0
           max(trip_distance): 9829.09
             max(fare_amount): 720.00
                   max(extra): 33.50
    1 row in set (1.84 sec)

    select count(*) from yellow_tripdata_2022_01 where trip_distance > 1000;
    +----------+
    | count(*) |
    +----------+
    |       68 |
    +----------+
    1 row in set (1.02 sec)

    root@localhost [23:37:23]> select trip_id, trip_distance, fare_amount, extra  from yellow_tripdata_2022_01 where trip_distance > 1000;
    +---------+---------------+-------------+-------+
    | trip_id | trip_distance | fare_amount | extra |
    +---------+---------------+-------------+-------+
    | 2393748 |      19626.57 |       16.21 |  0.00 |
    | 2393846 |      23724.06 |       27.20 |  0.00 |
    | 2394188 |      90081.19 |       13.20 |  0.00 |
    | 2394955 |      99999.99 |       21.88 |  0.00 |
    | 2395702 |      99999.99 |       13.20 |  0.00 |
    | 2396302 |      99999.99 |       13.44 |  0.00 |
    | 2398837 |      99999.99 |       29.98 |  0.00 |
    | 2400548 |      99999.99 |       24.82 |  0.00 |
    | 2400587 |      19916.99 |       15.81 |  0.00 |
    | 2401407 |      29311.90 |       13.20 |  0.00 |
    | 2405680 |      99999.99 |       21.86 |  0.00 |
    | 2407187 |      76839.92 |       53.66 |  0.00 |
    | 2408363 |       9829.09 |       19.89 |  0.00 |
    | 2408386 |      35783.82 |       13.20 |  0.00 |
    | 2408655 |      99999.99 |       13.20 |  0.00 |
    | 2409416 |      99999.99 |       14.96 |  0.00 |
    | 2414571 |      99999.99 |       15.40 |  0.00 |
    | 2414890 |      95666.46 |       14.22 |  0.00 |
    | 2415706 |      82340.33 |        8.26 |  0.00 |
    | 2416306 |      36181.15 |       12.72 |  0.00 |
    | 2417144 |      99999.99 |        7.70 |  0.00 |
    | 2417258 |      30650.30 |        7.70 |  0.00 |
    | 2418768 |      99999.99 |        8.31 |  0.00 |
    | 2419071 |      68016.95 |       23.33 |  0.00 |
    | 2419139 |      99999.99 |       11.03 |  0.00 |
    | 2420066 |      67058.18 |       10.56 |  0.00 |
    | 2420898 |      21367.20 |       10.73 |  0.00 |
    | 2422429 |      80474.82 |       19.73 |  0.00 |
    | 2424068 |       5447.67 |       15.41 |  0.00 |
    | 2424905 |      99999.99 |        7.70 |  0.00 |
    | 2425043 |      36221.72 |       17.61 |  0.00 |
    | 2427431 |      70004.76 |       17.89 |  0.00 |
    | 2428225 |      99999.99 |       20.60 |  0.00 |
    | 2429121 |      35254.55 |       57.98 |  0.00 |
    | 2429597 |      99999.99 |       13.74 |  0.00 |
    | 2429789 |       7653.16 |       14.54 |  0.00 |
    | 2430217 |      48760.50 |       18.27 |  0.00 |
    | 2430394 |      99999.99 |        7.70 |  0.00 |
    | 2430425 |      47635.84 |       19.22 |  0.00 |
    | 2435053 |      28046.23 |       13.82 |  0.00 |
    | 2435151 |      10503.93 |       12.39 |  0.00 |
    | 2438784 |      16536.51 |       15.52 |  0.00 |
    | 2438903 |       8139.12 |        8.12 |  0.00 |
    | 2444205 |      99999.99 |       17.70 |  0.00 |
    | 2445250 |      95093.06 |       17.83 |  0.00 |
    | 2445498 |      76869.06 |       10.64 |  0.00 |
    | 2448313 |       6523.25 |       13.04 |  0.00 |
    | 2448422 |      99999.99 |       10.10 |  0.00 |
    | 2448457 |      96113.91 |        7.70 |  0.00 |
    | 2448561 |       8665.17 |        7.70 |  0.00 |
    | 2448602 |      29103.20 |       31.55 |  0.00 |
    | 2448615 |      48132.95 |       19.49 |  0.00 |
    | 2449166 |      19417.20 |       17.31 |  0.00 |
    | 2453025 |      79700.98 |       15.05 |  0.00 |
    | 2453288 |      21212.60 |       20.85 |  0.00 |
    | 2453742 |      65743.99 |       64.78 |  0.00 |
    | 2453885 |      81334.13 |       30.87 |  0.00 |
    | 2454079 |      99999.99 |       13.71 |  0.00 |
    | 2454347 |      99999.99 |       20.13 |  0.00 |
    | 2454393 |      22972.95 |       22.92 |  0.00 |
    | 2454573 |      35595.76 |        9.12 |  0.00 |
    | 2455004 |      93552.26 |       33.08 |  0.00 |
    | 2456621 |      99999.99 |       26.29 |  0.00 |
    | 2457925 |      15013.51 |       10.66 |  0.00 |
    | 2458062 |      97161.52 |       14.92 |  0.00 |
    | 2461012 |      99999.99 |       27.71 |  0.00 |
    | 2461083 |      99999.99 |       28.58 |  0.00 |
    | 2461409 |      77616.82 |       17.80 |  0.00 |
    +---------+---------------+-------------+-------+
    68 rows in set (0.93 sec)


    mysql> select trip_id, trip_distance, fare_amount, extra  from yellow_tripdata_2022_01 where fare_amount > 500;
    +---------+---------------+-------------+-------+
    | trip_id | trip_distance | fare_amount | extra |
    +---------+---------------+-------------+-------+
    |  118190 |        254.88 |      668.00 |  0.50 |
    |  429859 |          3.30 |    99999.99 |  2.50 |
    |  942017 |        252.04 |      640.50 |  0.00 |
    | 1470782 |          0.00 |      720.00 |  0.00 |
    | 1524836 |        172.13 |      580.50 |  0.00 |
    | 1529947 |          0.00 |      538.00 |  0.00 |
    | 1722517 |        257.70 |      650.00 |  1.25 |
    | 2041808 |        184.69 |      624.00 |  0.00 |
    | 2245486 |        115.10 |      550.00 |  1.25 |
    +---------+---------------+-------------+-------+
    9 rows in set (0.98 sec)

    select max(tip_amount) from  yellow_tripdata_2022_01 where trip_distance < 10.00;
    +-----------------+
    | max(tip_amount) |
    +-----------------+
    |          888.88 |
    +-----------------+
    1 row in set (1.06 sec)

    select 'Airport', count(*) from yellow_tripdata_2022_01 where airport_fee > 0.0 union select 'Total', count(*) from yellow_tripdata_2022_01;
    +---------+----------+
    | Airport | count(*) |
    +---------+----------+
    | Airport |   158950 |
    | Total   |  2463931 |
    +---------+----------+
    2 rows in set (1.56 sec)

    select count(*) from yellow_tripdata_2022_01 where tpep_pickup_datetime < '2022-01-01 00:00:00';
    +----------+
    | count(*) |
    +----------+
    |       38 |
    +----------+
    1 row in set (0.83 sec)

    mysql> select date(tpep_pickup_datetime) as date, date_format(date(tpep_pickup_datetime),'%a') as weekday, count(*) as rides from yellow_tripdata_2022_01 where tpep_pickup_datetime >= '2022-01-01 00:00:00' and tpep_pickup_datetime < '2022-02-01 00:00:00' group by date(tpep_pickup_datetime), date_format(date(tpep_pickup_datetime),'%a') order by 1;
    +------------+---------+--------+
    | date       | weekday | rides  |
    +------------+---------+--------+
    | 2022-01-01 | Sat     |  63441 |
    | 2022-01-02 | Sun     |  58421 |
    | 2022-01-03 | Mon     |  72405 |
    | 2022-01-04 | Tue     |  74562 |
    | 2022-01-05 | Wed     |  74592 |
    | 2022-01-06 | Thu     |  79909 |
    | 2022-01-07 | Fri     |  71590 |
    | 2022-01-08 | Sat     |  83177 |
    | 2022-01-09 | Sun     |  64014 |
    | 2022-01-10 | Mon     |  73692 |
    | 2022-01-11 | Tue     |  77603 |
    | 2022-01-12 | Wed     |  80352 |
    | 2022-01-13 | Thu     |  84952 |
    | 2022-01-14 | Fri     |  93817 |
    | 2022-01-15 | Sat     |  88704 |
    | 2022-01-16 | Sun     |  72783 |
    | 2022-01-17 | Mon     |  63518 |
    | 2022-01-18 | Tue     |  84603 |
    | 2022-01-19 | Wed     |  86640 |
    | 2022-01-20 | Thu     |  90778 |
    | 2022-01-21 | Fri     | 101054 |
    | 2022-01-22 | Sat     |  96587 |
    | 2022-01-23 | Sun     |  76914 |
    | 2022-01-24 | Mon     |  78541 |
    | 2022-01-25 | Tue     |  87349 |
    | 2022-01-26 | Wed     |  96747 |
    | 2022-01-27 | Thu     |  99766 |
    | 2022-01-28 | Fri     |  95873 |
    | 2022-01-29 | Sat     |  34388 |
    | 2022-01-30 | Sun     |  71229 |
    | 2022-01-31 | Mon     |  85878 |
    +------------+---------+--------+
    31 rows in set (2.35 sec)

    mysql> select date_format(date(tpep_pickup_datetime),'%a') as weekday, count(*) as rides from yellow_tripdata_2022_01 where tpep_pickup_datetime >= '2022-01-01 00:00:00' and tpep_pickup_datetime < '2022-02-01 00:00:00' group by date_format(date(tpep_pickup_datetime),'%a') order by 2 DESC;

    select date_format(date(tpep_pickup_datetime),'%a') as weekday, count(*) as rides from yellow_tripdata_2022_01 where tpep_pickup_datetime >= '2022-01-01 00:00:00' and tpep_pickup_datetime < '2022-02-01 00:00:00' group by date_format(date(tpep_pickup_datetime),'%a') order by 2 DESC;
    +---------+--------+
    | weekday | rides  |
    +---------+--------+
    | Mon     | 374034 |
    | Sat     | 366297 |
    | Fri     | 362334 |
    | Thu     | 355405 |
    | Sun     | 343361 |
    | Wed     | 338331 |
    | Tue     | 324117 |
    +---------+--------+
