# Federal Reserve, EIA, and Financial Analyses

### Summary
This repo contains a series of generic Python scripts which fetch data from various API's including FRED (Federal Reserve), EIA, and more, and store this in a Postgres database. Subsequently, it contains script which read and analyze this data, as well as predictions. This is not a centralized application, but instead an extract of various scripts used within a financial web application I've been building, which will be released separately.

Developed using:

[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)](#) [![Postgres](https://img.shields.io/badge/Postgres-%23316192.svg?logo=postgresql&logoColor=white)](#) [![Pandas](https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=fff)](#) [![NumPy](https://img.shields.io/badge/NumPy-4DABCF?logo=numpy&logoColor=fff)](#) 

These scripts belong to a centralized utility I've developed which is used to run the scripts on schedules and export the data as well as analyze it, however, I have not included that utility within this repo at this time. This is solely a collection of some of the scripts which I've chosen to share for public use. This repository will be continuously enhanced as I find need to add more scripts and predictions. 

### Configuration
- Install the dependency libraries in requirements.txt. _(pip install -r requirements.txt)_
- Credentials can be stored and configured in a .env file. A .env.dev file has been included with a template of the credentials.
- Various keys may be required depending on which script is being run. These keys can be retrieved for free. They are the: FRED API Key, EIA API Key, and CoinGecko API Key. Usage limitations may apply.
- Presidential data may need to be updated as terms change. There are 2 locations: the presidential_terms Postgres table, and the JSON file inside of the web directory which contains the federal debt as a value % of the GDP.
- Tables are configured and created via the table_configuration.sql file. Since this is not a web application, the file will need to be run manually or initialized via the install_postgres_cnfg.py script.
- There is an "engines" table which can track the statuses of each integrated scrypt if desired. This table can be built upon for any web app design if desired, but if you run these scripts on a scheduler, ensure the initEngines script is also run to track the statusing and timestamps of each other script. This is essentially the monitoring utility.

Numerous libraries used including:
- pandas
- numpy
- sqlalchemy 
- psycopg2-binary 
- python-dotenv
- dash
- dash-bootstrap-components
- statsmodels
- yfinance 
- fredapi

**NOTE:** Some analyses are automatically configured with Dash and/or Matplotlib. If you don't wish to run the analyses scripts within that directory, simply ignore those libraries and don't install them.

------------

### Data Samples
Numerous different types of output are generated from these scripts. While most are used in a centralized web app, some are generic output graphs. I've provided samples below which I've personally found intriguing that are output from various scripts here, and/or the data in the database after using these scripts. Feel free to use these in the future in any capacity. More can be found in the export/img/ sub-directories.

Housing Data:
- ![housing_2019-now](https://github.com/user-attachments/assets/7ff39c57-e0bc-47d4-8936-1aa6b3598b70)
- ![housing_2014-now](https://github.com/user-attachments/assets/b7d16ebd-327a-44f0-ae58-8bd6472c903c)
- ![housing_1999-now](https://github.com/user-attachments/assets/a6a24e14-8d64-41c4-98b4-3cbda60196b4)
- ![housing_1975-now](https://github.com/user-attachments/assets/dc26a6c2-7dad-4fcf-acb5-8fcd09b894fd)

US Oil Against Inflation:
- ![us_oil_v_inflation](https://github.com/user-attachments/assets/a4a9e913-b1ab-4851-990c-9e867e0c4921)
