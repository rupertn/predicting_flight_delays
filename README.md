# Will Your Flight Be Delayed?
### Project Overview
  - Scraped more than 5000 aircraft registrations from the FAA website using python and beautifulsoup.
  - Engineered features from aviation weather report text (METARs) to indicate the presence of fog or a thunderstorm at the scheduled departure time.
  - Performed a complex T-SQL join of the flight and weather data on the closest weather report timestamp to the scheduled departure time.
  - Optimized logistic regression, decision tree, and random forest models using GridSearchCV to improve model performance in an unbalanced classifcation problem.
## Tools and Resources Used
**Python**: 3.8  
**Packages**: numpy, pandas, matplotlib, seaborn, sklearn, beautifulsoup4, grequests  
**SQL Server**: 2019
## Data Collection
  - 
### FAA Aircraft Registration Web Scraper

For each aircraft tail number, also known as an N-number, the following registration information was collected:
  - Active Aircraft
    - Aircraft Model
    - Engine Model
    - Manufacturer Year
  - Deregistered Aircraft
    - Manufacturer Year
    - Registration Cancellation Date
    
To reduce load on the server, requests were sent in batches of 10 rather than individually as we have thousands of unique urls.  
## Data Cleaning
## Exploratory Data Analysis
## Model Building
## Closing Remarks
