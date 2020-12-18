# Will Your Flight Be Delayed?
### Project Overview
  * PURPOSE 
  * Scraped more than 5000 aircraft registrations from the FAA website using python and beautifulsoup.
  * Engineered features from aviation weather report text (METARs) to indicate the presence of fog or thunderstorms at the scheduled departure time.
  * Performed a complex T-SQL join of the flight and weather data on the closest weather report timestamp to the scheduled departure time.
  * Optimized logistic regression, decision tree, and random forest models using GridSearchCV to improve model performance in an unbalanced classifcation problem. 
  
  ![](san_francisco_airport.jpg)
## Tools and Resources Used
**Python**: 3.8  
**Packages**: numpy, pandas, matplotlib, seaborn, sklearn, beautifulsoup4, grequests  
**SQL Server**: 2019  
**Calculating Greatest Circle Distance**: [https://medium.com/analytics-vidhya/finding-nearest-pair-of-latitude-and-longitude-match-using-python-ce50d62af546](https://medium.com/analytics-vidhya/finding-nearest-pair-of-latitude-and-longitude-match-using-python-ce50d62af546)  

## Data Collection  
If a domestic flight was delayed in the United States in 2019, the delay typically fell into to one of four main categories, a weather delay (high winds, thunderstorms, freezing rain etc.), an airline delay (mechanical problem, crew scheduling issue etc.), a late aircraft delay (schedule knock-on effects etc.), or an air system delay (airport congestion, waiting for de-icing or refueling services etc.).  

To accurately predict if a flight would be delayed several hours prior to its departure, we need data that relates to each type of commonly experienced delay. The following data sources were decided upon:  

  * **Airline On-Time Performance Data**
      * Source: [United States Department of Transportation (Bureau of Transportation Statistics)](https://www.transtats.bts.gov/Tables.asp?DB_ID=120&DB_Name=Airline%20On-Time%20Performance%20Data&DB_Short_Name=On-Time)
  * **Airport Weather Reports from FAA Managed Weather Stations**
      * Source: [National Centers for Environmental Information - U.S. Local Climatological Data (LCD)](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C00684)
  * **Aircraft Registration Data**  
      * Source: web scraped via the FAA aircraft registration website.  
  * **Airport Locations**
      * Source: [https://github.com/datasets/airport-codes](https://github.com/datasets/airport-codes)
  
    
### FAA Aircraft Registration Web Scraper

For each aircraft tail number, also known as an N-number, the following registration information was collected:
  * Active Aircraft:
    * Aircraft Model
    * Engine Model
    * Manufacturer Year
  * Deregistered Aircraft:
    * Manufacturer Year
    * Registration Cancellation Date
    
To reduce load on the server, requests were sent in batches of 10 rather than individually as we have thousands of unique urls.  
## Data Cleaning
**Airline On-Time Performance Data:**
  * Created columns to indicate if the departure or arrival airport was slot controlled.
  * Determined which flights were operated by a swapped aircraft, and removed them.
    * Removed because the tail number assigned to each flight was of the aircraft that actually operated the flight, and not necessarily the one that caused the delay. 
  * Adjusted aircraft tail numbers to ensure they all begin with 'N'.
  * Created a list of all unique tail numbers in the dataset to feed into the aircraft registration scraper.
  * Created a column to indicate if the previous flight was delayed.

**Airport Weather Reports:**
  * Created columns from METAR text to indicate the presence of fog, thunderstorms, or rain. 
  * Used regular expressions to extract the numerical component of the recorded wind speed.
  * Conformed all visibility entries to the aviation standard of 0 - 10 statute miles.  

**Scraped Aircraft Registration Data:**  
  * Used regular expressions to remove all year and date values that had incorrect formatting.
  * Built a function to identify the correct manfucturer year for tail numbers that had multiple aircraft on the registration record. 
  * Calculated the approximate aircraft age in August 2019. 
  
**Airport Location Data:**
  * Filtered the data to contain only the unique airports found in the Airline On-Time Performance Data.
  * For each unique airport, determined the closest weather station based on latitude and longitude.  
  * Identified if the assigned weather station was correct using regular expressions, followed with a manual review. 

### Joining Cleaned Data  
Given the quantity and size of the data sources used, along with the desired structure of the combined dataframe, I felt using SQL Server to join the data sources would be more straightforward than using python. The most complex step was joining the on-time performance and weather report data based on the closest weather report time to the scheduled departure time of each flight. Across all flights, a mean differential of 16 minutes was achieved.

## Exploratory Data Analysis
![](aircraft_age_dist.png)
![](delays_by_hour.png) ![](thunderstorm_delays.png)![](corr_matrix.png)

## Model Building
The classification models I wanted to explore were logistic regression, decision tree, and random forest models. In theory, with an imbalanced dataset (4 to 1 ratio of non-delayed flights to delayed flights) and some multicollinearity between features, a random forest model was expected to perform well. I chose to exclude support vector machines as the run time would be slow on a dataset of this size. 

First, I tested each model using the default parameters, then using GridSearchCV, adjusted hyperparameters to optimize the model performance. Model performance was evaluate with the F-score as both precision and recall were important. I was primarily interested in maximizing recall (the share of delayed flights the model correctly predicted) without significantly sacrificing precision. 

Unfortunately, I found that each model was good at predicting non-delayed flights, but fairly poor at predicting delayed flights. The best performing model was a random forest model that achieved an F-score of 0.91 for class 0 and 0.52 for class 1.

## Closing Remarks

- Need to look at a full years worth of data. One airline may have a bad month due organizational problems.. 
- Weather may play a larger role in delays during the winter months
- Missing features that can't be calculated. Airlines holding flights for groups of delayed transiting passengers.
- Random events play a large role, aircraft mechanical problems
- Not a large enough sample for extreme weather events (high winds)
