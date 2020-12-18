import pandas as pd
import grequests
from bs4 import BeautifulSoup

# importing a list of the unique tail numbers in the file airport_flights_aug2019.csv
tail_nums = pd.read_csv('/Data/Interim/unique_tail_nums.csv')

ac_info = []
urls = []

# creating a list of urls for tail numbers. A few numbers have no 'N' preceding the identifier.
for t_num in tail_nums['tail_num'].tolist():
    if list(t_num)[0] != 'N':
        n_num = t_num
    else:
        n_num = t_num.split('N', 1)[1]

    url = 'https://registry.faa.gov/AircraftInquiry/Search/NNumberResult?nNumberTxt=' + n_num
    urls.append(url)


# Function to acquire aircraft registration information.
def get_ac_info(reg):
    soup = BeautifulSoup(reg.text)
    tail_info = ['N' + reg.url.split('=')[1]]

    attributes = ["Model", "Engine Model", "Mfr Year", "Year Manufacturer", "Cancel Date"]

    for attribute in attributes:
        # If soup.find() doesn't find the attribute it returns None.
        tail_info.append(soup.find(attrs={"data-label": attribute}).get_text())

    ac_info.append(tail_info)


# function to print failed requests
def exception_handler(request, exception):
    print("Request failed")


# sending groups of requests at the same time for improved performance
rs = (grequests.get(u) for u in urls)
registrations = grequests.map(rs, exception_handler=exception_handler, size=10)

# acquiring aircraft info for each tail number
for registration in registrations:
    get_ac_info(registration) 

# assigning data to a pandas dataframe
ac_info = pd.DataFrame(ac_info, columns=['tail', 'ac_model', 'eng_model', 'man_yr', 'dreg_man_yr', 'cncl_date'])

# exporting data to a csv file
ac_info.to_csv('/Data/Raw/scraped_aircraft_info.csv', index=False)
