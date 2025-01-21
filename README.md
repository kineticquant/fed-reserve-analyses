# Federal Reserve Analyses
This repo contains a generic scripted setup using Python to get API's of data from FRED (Federal Reserve) via the API, store in Postgres DB, and analyze.

These scripts belong to a centralized tool used to run the scripts on schedules and export the data as well as analyze it, however, I have not included that utility within this repo at this time. This is solely a collection of some of the scripts which I've chosen to share for public use.

Credentials can be stored and configured in a .env file. A .env.dev file has been included with a template of the credentials. 

The utility also contains scripts gathering data from Coingecko and EIA. Some scripts analyzing these are not included as they're part of a larger financial analysis tool. Simply place the API keys for each of these systems into the .env file.


------------

Data samples:
