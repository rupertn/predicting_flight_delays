CREATE DATABASE [flight_delays];

USE [flight_delays];

-- Using the import wizard, imported the following tables after python cleaning:
        --  aircraft: tail number and ages
        --  flights: origin, destination, dep and arr times, delays etc.
        --  stations: weather stations matching to the airport codes.
        --  weather: all METAR reports for the airports.

-- Adding foreign keys to the flights table.
ALTER TABLE flights
ADD CONSTRAINT origin_fk FOREIGN KEY (origin) REFERENCES stations (iata_code),
CONSTRAINT dest_fk FOREIGN KEY (dest) REFERENCES stations (iata_code),
CONSTRAINT tail_num_fk FOREIGN KEY (tail_num) REFERENCES aircraft (tail_num);


-- Joining the flights, aircraft, and weather station tables as I will use this table frequently.
SELECT * INTO flights_aircraft_stations
FROM
    (SELECT f.*, a.aircraft_age, s1.matched_stn_name AS dep_station, s2.matched_stn_name AS arr_station
    FROM flights f
    INNER JOIN aircraft a
    ON f.tail_num = a.tail_num
    INNER JOIN stations s1
    ON f.origin = s1.iata_code
    INNER JOIN stations s2
    ON f.dest = s2.iata_code
    WHERE s1.correct_match = 1 AND s2.correct_match = 1) flights_aircraft_stations;


-- Identifying the departure weather report closest to the departure time for each flight and returning the desired columns.
SELECT t1.crs_dep_datetime, 
       t1.crs_dep_date,
       t1.crs_dep_time,
       t1.dep_hour AS crs_dep_hour,
       t1.crs_arr_datetime,
       t1.crs_arr_date,
       t1.crs_arr_time,
       t1.mkt_carrier_airline_id,
       t1.mkt_carrier,
       t1.mkt_carrier_fl_num,
       t1.origin,
       t1.dest,
       t1.dep_slot_controlled,
       t1.arr_slot_controlled,
       t1.origin_airport_id,
       t1.dest_airport_id,
       t1.origin_city_name,
       t1.dest_city_name,
       t1.origin_city_market_id,
       t1.dest_city_market_id,
       t1.origin_state_nm,
       t1.dest_state_nm,
       t1.tail_num,
       t1.dep_del15,
       t1.prev_fl_del,
       t1.aircraft_age,
       t1.dep_station,
       t1.arr_station,
       t1.report_datetime AS dep_report_datetime,
       t1.report_date AS dep_report_date,
       t1.report_time AS dep_report_time,
       t1.wind_speed AS dep_wind_speed,
       t1.wind_gust_speed AS dep_wind_gust_speed,
       t1.visibility AS dep_visibility,
       t1.fog AS dep_fog,
       t1.thunderstorm AS dep_thunderstorm,
       t1.rain AS dep_rain,
       t1.dep_w_diff
FROM
    (SELECT *, ABS(DATEDIFF(MINUTE, w.report_datetime, f.crs_dep_datetime)) AS dep_w_diff
    FROM flights_aircraft_stations f
    INNER JOIN weather w 
    ON f.dep_station = w.station_name AND f.crs_dep_date = w.report_date) t1
INNER JOIN
    (SELECT tail_num, crs_dep_datetime, crs_arr_datetime, origin, dest, MIN(ABS(DATEDIFF(MINUTE, w.report_datetime, f.crs_dep_datetime))) AS dep_w_diff
    FROM flights_aircraft_stations f
    INNER JOIN weather w 
    ON f.dep_station = w.station_name AND f.crs_dep_date = w.report_date
    GROUP BY tail_num, crs_dep_datetime, crs_arr_datetime, origin, dest) t2
ON t1.tail_num = t2.tail_num AND t1.crs_dep_datetime = t2.crs_dep_datetime AND t1.crs_arr_datetime = t2.crs_arr_datetime 
AND t1.origin = t2.origin AND t1.dest = t2.dest AND t1.dep_w_diff = t2.dep_w_diff;

-- Results of the last query exported to csv for use in the notebook "Predicting Flight Delays".
-- Note: The exported csv contains duplicates as more than one weather report may be "closest" to the departure time of a flight.
-- Returning multiple weather reports for the same flight can be prevented using the following query structure:

SELECT *
FROM
    (SELECT ROW_NUMBER() OVER(PARTITION BY f.tail_num, f.crs_dep_datetime, f.crs_arr_datetime, f.origin, f.dest ORDER BY ABS(DATEDIFF(MINUTE, w.report_datetime, f.crs_dep_datetime))) AS row_num, *
    FROM flights_aircraft_stations f
    INNER JOIN weather w
    ON f.dep_station = w.station_name AND f.crs_dep_date = w.report_date) X
WHERE row_num = 1;

-- However, due the table structure and disk space limitations this query would not complete on my machine. Instead, I will simply
-- drop the duplicates rows in python. 

