import numpy as np
import pandas as pd
import datetime as dt
from math import radians, cos, sin, asin, sqrt

# Assigning all columns of mixed data types to string for easy manipulation.
dtype = {'STATION': 'str', 'SOURCE': 'str', 'HourlyRelativeHumidity': 'str', 'HourlyPressureTendency': 'str',
         'HourlyWetBulbTemperature': 'str', 'HourlyWindGustSpeed': 'str', 'Sunrise': 'str', 'Sunset': 'str'}

# Importing airport weather reports
w = pd.read_csv('Data/Raw/airport_weather.csv', dtype=dtype)

w = w.rename(columns={'NAME': 'station_name', 'DATE': 'report_datetime', 'HourlyWindSpeed': 'wind_speed',
                      'HourlyWindGustSpeed': 'wind_gust_speed', 'HourlyVisibility': 'visibility',
                      'HourlyPresentWeatherType': 'hourly_present_weather_type'})

# Converting all columns titles to lowercase
w.columns = map(str.lower, w.columns)

# Converting to datetime data type and creating separate columns for the report date and time
w[['report_date', 'report_time']] = w.report_datetime.str.split('T', 1, expand=True)
w['report_datetime'] = w['report_datetime'].replace('T', ' ')
w['report_datetime'] = pd.to_datetime(w['report_datetime'])

# Extracting the numerical component of each entry in the wind speed columns. If there was no entry for wind speed
# I assumed a value of 0. If the wind gust speed was a null value I assumed that its value was equal to the
# corresponding wind speed for that entry.
regex = r'^(\d{1,2})$'
w['wind_speed'] = w.wind_speed.str.extract(regex).fillna('0')
w['wind_gust_speed'] = w.wind_gust_speed.str.extract(regex)
w['wind_gust_speed'] = w['wind_gust_speed'].fillna(w['wind_speed'])

# Extracting the numerical component of each visibility entry. METAR visibility typically ranges from 0-10 SM, thus
# any value exceeding 10 SM was replaced with 10 SM. Null entries were also replaced with 10 SM.
regex = r'^((\d|10)(\.\d+)?)$'
w['visibility'] = w.visibility.str.extract(regex).fillna('10')

# Creating three binary columns to indicate the presence of Fog, Thunderstorm, or Rain in the METARs.
w['fog'] = w['hourly_present_weather_type'].apply(lambda x: 1 if 'FG' in str(x) else 0)
w['thunderstorm'] = w['hourly_present_weather_type'].apply(lambda x: 1 if 'TS' in str(x) else 0)
w['rain'] = w['hourly_present_weather_type'].apply(lambda x: 1 if 'RA' in str(x) else 0)

# Converting all numerical columns with a string data type to a numerical data type.
w['wind_speed'] = w['wind_speed'].astype(int)
w['wind_gust_speed'] = w['wind_gust_speed'].astype(int)
w['visibility'] = w['visibility'].astype(float)

w_out = w[['station_name', 'report_datetime', 'report_date', 'report_time', 'wind_speed', 'wind_gust_speed',
           'visibility', 'fog', 'thunderstorm', 'rain']]

w_out.to_csv('/Data/Interim/airport_weather_cleaned.csv', index=False)

# ----------------------------------------------

# Importing all US domestic flights from August 2019
f = pd.read_csv('/Data/Raw/airport_flights.csv')

f.columns = map(str.lower, f.columns)

# Dropping all rows containing nulls values. Nulls are primarily from cancelled flights, which we are not interest in.
f.drop('unnamed: 20', axis=1, inplace=True)
f.dropna(inplace=True)

# Determining if the departure or arrival airport of each flight has slot restrictions.
slot_control_ap = ['JFK', 'DCA', 'LGA', 'EWR', 'SFO', 'LAX', 'ORD']
f['dep_slot_controlled'] = f['origin'].apply(lambda x: 1 if x in slot_control_ap else 0)
f['arr_slot_controlled'] = f['dest'].apply(lambda x: 1 if x in slot_control_ap else 0)

# The fl_date is the same as the crs_dep_date therefore I renamed the column for better clarity.
f.rename(columns={'fl_date': 'crs_dep_date'}, inplace=True)
f['crs_dep_date'] = pd.to_datetime(f['crs_dep_date'])
f[['dep_time', 'arr_time', 'dep_del15']] = f[['dep_time', 'arr_time', 'dep_del15']].astype(int)

# Changing midnight dep and arr time readings from 2400 to 0.
f.loc[f['dep_time'] == 2400, 'dep_time'] = 0
f.loc[f['arr_time'] == 2400, 'arr_time'] = 0


# Function to identify if a flight arrived before it departed (caused by timezone changes).
# No US domestic flight is longer than 10 hours and no time change can be greater than 6 hours, therefore any arr time
# before the dep time but within 8 hours must have arrived the same day before departure.
def arr_before_dep(dep, arr):
    if (dep >= arr) & ((dep - arr) < 800):
        return 1
    else:
        return 0 


# Function to return the correct crs arrival date for each flight.
def get_crs_arr_date(crs_dep_date, crs_dep, crs_arr):
    if (arr_before_dep(crs_dep, crs_arr) == 1) | (crs_dep < crs_arr):
        return crs_dep_date
    else:
        return crs_dep_date + pd.Timedelta(days=1)


# Some flights departed early therefore early departures within 1 hour of the crs dep time were considered
# as a same day departure. Consequently, this means the function assumes no flight was delayed more than 23 hours.
def get_dep_date(crs_dep_date, crs_dep, dep):
    if (dep > crs_dep) | ((crs_dep - dep) < 100):
        return crs_dep_date
    else:
        return crs_dep_date + pd.Timedelta(days=1)


f['dep_date'] = f.apply(lambda row: get_dep_date(row['crs_dep_date'], row['crs_dep_time'], row['dep_time']), axis=1)
f['crs_arr_date'] = f.apply(lambda row: get_crs_arr_date(row['crs_dep_date'], row['crs_dep_time'],
                                                         row['crs_arr_time']), axis=1)

# Converting date and time columns to strings to allow for conversion to datetime objects.
to_string = ['crs_dep_date', 'crs_arr_date', 'dep_date', 'crs_dep_time', 'crs_arr_time', 'dep_time']

for col in to_string:
    f[col] = f[col].astype(str) 


# A function to convert times of 1-4 char length (ex. 154 or 1738) to 24 hour clock (ex. 01:54:00, 17:38:00)
def format_time(t):
    if len(t) == 4:
        return t[0:2] + ':' + t[2:] + ':00'
    elif len(t) == 3:
        return '0' + t[0] + ':' + t[1:] + ':00'
    elif len(t) == 2:
        return '00:' + t + ':00'
    else:
        return '00:0' + t + ':00'


# Formatting times to the 24 hours clock (ex. 150 -> 01:50:00).
format_time_cols = ['crs_dep_time', 'crs_arr_time', 'dep_time']

for col in format_time_cols:
    f[col] = f[col].apply(lambda x: format_time(x))         

# Creating a datetime object for dep and arr date and times (for both scheduled and actual).
f['crs_dep_datetime'] = pd.to_datetime(f['crs_dep_date'] + ' ' + f['crs_dep_time'])
f['crs_arr_datetime'] = pd.to_datetime(f['crs_arr_date'] + ' ' + f['crs_arr_time'])
f['dep_datetime'] = pd.to_datetime(f['dep_date'] + ' ' + f['dep_time'])

# Identifying the departure hour for each flight.
f['dep_hour'] = f['crs_dep_datetime'].dt.hour

# Reordering columns for easier reading.
cols_order = ['crs_dep_datetime', 'crs_dep_date', 'crs_dep_time', 'dep_hour', 'crs_arr_datetime', 'crs_arr_date',
              'crs_arr_time', 'dep_datetime', 'dep_date', 'dep_time', 'arr_time', 'mkt_carrier_airline_id',
              'mkt_carrier', 'mkt_carrier_fl_num', 'origin', 'dest', 'dep_slot_controlled', 'arr_slot_controlled',
              'origin_airport_id', 'dest_airport_id', 'origin_city_name', 'dest_city_name', 'origin_city_market_id',
              'dest_city_market_id', 'origin_state_nm', 'dest_state_nm', 'tail_num', 'dep_del15']

f = f[cols_order]

# Importing airport timezone data.
tz = pd.read_csv('/Data/Raw/airport_timezones.csv')

# Joining the correct origin and destination airport timezone for each flight.
f = f.merge(tz, left_on='origin', right_on='iata_code')
f = f.merge(tz, left_on='dest', right_on='iata_code')

# Dropping timezones columns of no interest and renaming columns of interest.
f.drop(['iata_code_x', 'windows_tz_x', 'iata_code_y', 'windows_tz_y'], axis=1, inplace=True)
f.rename(columns={'iana_tz_x': 'origin_tz', 'iana_tz_y': 'dest_tz'}, inplace=True)

# Creating new dep and arr time columns where times are converted to utc time. 
f['utc_crs_dep_datetime'] = f.apply(lambda row: row.crs_dep_datetime.tz_localize(row.origin_tz), axis=1)
f['utc_crs_arr_datetime'] = f.apply(lambda row: row.crs_arr_datetime.tz_localize(row.dest_tz), axis=1)
f['utc_dep_datetime'] = f.apply(lambda row: row.dep_datetime.tz_localize(row.origin_tz), axis=1)

# Converting utc time columns from string to utc datetime object.
for col in ['utc_crs_dep_datetime', 'utc_crs_arr_datetime', 'utc_dep_datetime']:
    f[col] = pd.to_datetime(f[col], utc=True)

# Sorting dataframe by tail_num then utc_arr_datetime to identify the correct order of flights flown by each aircraft.
f = f.sort_values(['tail_num', 'utc_dep_datetime'])

# Determining if the previous flight had a delayed departure.
f['prev_fl_del'] = f.groupby('tail_num')['dep_del15'].shift().fillna(0).astype(int)

# Identifying flights that were operated by a swapped aircraft. 
f['utc_crs_arr_shifted'] = f.groupby('tail_num')['utc_crs_arr_datetime'].shift()
f['arr_dep_diff'] = (f['utc_crs_dep_datetime'] - f['utc_crs_arr_shifted']).fillna(pd.Timedelta(hours=1))
f['aircraft_swap'] = f['arr_dep_diff'].apply(lambda x: 1 if x < pd.Timedelta(minutes=20) else 0)

# Ensuring all N-numbers starting with an N.
f['tail_num'] = f['tail_num'].apply(lambda x: x if x.startswith('N') else 'N' + x)

# Before moving on, I require a csv containing all the unique tail numbers in the flight data to feed
# into my aircraft registration scraper.
unique_tail_nums = f['tail_num'].unique()
utn = pd.DataFrame(unique_tail_nums, columns=['tail_num'])
utn.to_csv('/Data/Raw/unique_tail_nums.csv', index=False)

# Removing all rows where the flights was operated by a swapped aircraft.
f = f[f['aircraft_swap'] == 0]

f_out = f.drop(['origin_tz', 'dest_tz', 'utc_crs_dep_datetime', 'utc_crs_arr_datetime', 'dep_datetime', 'dep_date',
                'dep_time', 'arr_time', 'utc_dep_datetime', 'utc_crs_arr_shifted', 'arr_dep_diff',
                'aircraft_swap'], axis=1)

f_out.to_csv('/Data/Interim/airport_flights_cleaned.csv', index=False)

# ----------------------------------------------

# Importing airport information
ap = pd.read_csv('/Data/Raw/airport_info.csv')

ap = ap.rename(columns={'name': 'airport_name'})

ap[['lon', 'lat']] = ap.coordinates.str.split(', ', expand=True)
ap[['lon', 'lat']] = ap[['lon', 'lat']].astype(float)

# To identify the correct weather station for each airport I need a list of all uniques airports in the flight data.
unique_airports = pd.concat([f['origin'], f['dest']]).drop_duplicates().tolist()

# Filtering for airport data to select only the airports in the flight data.
ap = ap.loc[ap['iata_code'].isin(unique_airports), ['iata_code', 'airport_name', 'lat', 'lon']]

# Identifying all unique weather stations and their locations.
w_stations = w[['station_name', 'latitude', 'longitude']].drop_duplicates()


# Calculate the great circle distance between two points on the earth (specified in decimal degrees)
def dist(lat1, long1, lat2, long2):
    # convert decimal degrees to radians 
    lat1, long1, lat2, long2 = map(radians, [lat1, long1, lat2, long2])
    # haversine formula 
    dlon = long2 - long1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    km = 6371 * c
    return km


# Function to find the nearest weather station to each airport
def find_nearest_station(lat, long):
    distances = w_stations.apply(
        lambda row: dist(lat, long, row['latitude'], row['longitude']), axis=1)
    return w_stations.loc[distances.idxmin(), 'station_name']


# Matching the nearest weather station to each airport.
ap['matched_stn_name'] = ap.apply(lambda row: find_nearest_station(row['lat'], row['lon']), axis=1)

# Attempting to identify if the matched weather station for each airport is correct. Unfortunately, as most airport
# and weather station names are not a perfect match, manual review of results will be required.
ap['correct_match'] = ap.apply(lambda row: 1 if row.airport_name.upper() in row.matched_stn_name else 0, axis=1)

ap_out = ap[['iata_code', 'airport_name', 'matched_stn_name']]

ap_out.to_csv('/Data/Interim/matched_weather_stns.csv', index=False)

# ----------------------------------------------

# Importing scraped aircraft registration information
ac = pd.read_csv('/Data/Raw/scraped_aircraft_info.csv')

ac = ac.rename(columns={'tail': 'tail_num'})

# Replacing strings that do not conform to the year and date regular expressions with a null or empty string.
yr_regex = r'^((19|20)\d{2})$'
ac.man_yr = ac.man_yr.str.extract(yr_regex)
ac.dreg_man_yr = ac.dreg_man_yr.str.extract(yr_regex)

date_regex = r'^((0[1-9]|1[012])[\/](0[1-9]|[12][0-9]|3[01])[\/](19|20)\d{2})$'
ac.cncl_date = ac.cncl_date.str.extract(date_regex).fillna("")


# Function to identify the correct manufacturer year for N-numbers that have multiple aircraft on the record.
def get_correct_year(yr1, yr2, c_date):
    if not c_date:
        # dummy date to allow for string split to occur. Date guarantees return of yr1 at elif statement.
        c_date = '1/1/1900'
    c_date = c_date.split('/')
    year, month, day = int(c_date[2]), int(c_date[0].lstrip('0')), int(c_date[1].lstrip('0'))

    if yr2 is None:
        return yr1
    elif dt.date(2019, 8, 1) > dt.date(year, month, day):
        return yr1
    else:
        return yr2


ac['correct_man_yr'] = ac.apply(lambda row: get_correct_year(row['man_yr'], row['dreg_man_yr'],
                                                             row['cncl_date']), axis=1)

# Calculating the approximate aircraft age (+- ~6 months) at the beginning of August 2019.
ac['correct_man_yr'] = pd.to_datetime(ac['correct_man_yr'] + '-06-30', errors='coerce')
ac['aircraft_age'] = ac['correct_man_yr'].apply(lambda x: pd.to_datetime('2019-08-01') - x)
ac['aircraft_age'] = round(ac['aircraft_age'] / np.timedelta64(1, 'Y'), 0)

ac_out = ac[['tail_num', 'aircraft_age']]

ac_out.to_csv('/Data/Interim/aircraft_ages.csv', index=False)
