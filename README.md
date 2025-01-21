# Federal Reserve Analyses

### Summary
This repo contains a generic scripted setup using Python to get API's of data from FRED (Federal Reserve) via the API, store in Postgres DB, and analyze.

These scripts belong to a centralized tool used to run the scripts on schedules and export the data as well as analyze it, however, I have not included that utility within this repo at this time. This is solely a collection of some of the scripts which I've chosen to share for public use.

Credentials can be stored and configured in a .env file. A .env.dev file has been included with a template of the credentials. 

The utility also contains scripts gathering data from Coingecko and EIA. Some scripts analyzing these are not included as they're part of a larger financial analysis tool. Simply place the API keys for each of these systems into the .env file.

Tables are configured and created via the table_configuration.sql file. Since this is not a web application, the file will need to be run manually or initialized via the install_postgres_cnfg.py script.

There is an "engines" table which can track the statuses of each integrated scrypt if desired. This table can be built upon for any web app design if desired.

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

Some analyses are automatically configured with Dash and/or Matplotlib. If you don't wish to run the analyses scripts within that directory, simply ignore those libraries and don't install them.

------------

Data samples:
