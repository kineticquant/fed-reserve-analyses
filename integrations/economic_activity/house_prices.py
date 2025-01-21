import pandas as pd
from fredapi import Fred
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
fredk = os.getenv('FREDK')

engine_status = 'In Progress'

# Median
HOUSE_PRICES_SERIES_ID = 'MSPUS'  # FRED series ID for median house prices

# Average
AVG_HOUSE_PRICES_SERIES_ID = 'ASPUS'  # FRED series ID for average house prices

# Initialize Fred API client
try:
    fred = Fred(api_key=fredk)
    print("Successfully connected to FRED API client.")
    engine_status = 'Success'
except Exception as e:
    print(f"Error initializing Fred API client: {e}")
    engine_status = 'Error'
    exit()

# Fetch median house prices data
try:
    median_house_prices_data = fred.get_series(HOUSE_PRICES_SERIES_ID)
    print("Successfully fetched median house prices data from FRED API.")
    # Convert to DataFrame
    median_house_prices_df = pd.DataFrame(median_house_prices_data, columns=['Median_House_Price'])
    median_house_prices_df.index.name = 'Date'
    median_house_prices_df.reset_index(inplace=True)
    # Add quarter column
    median_house_prices_df['Quarter'] = median_house_prices_df['Date'].dt.to_period('Q').dt.strftime('Q%q-%Y')

except Exception as e:
    print(f"Error fetching median house prices data: {e}")
    engine_status = 'Error'
    exit()

# Fetch average house prices data
try:
    avg_house_prices_data = fred.get_series(AVG_HOUSE_PRICES_SERIES_ID)
    print("Successfully fetched average house prices data from FRED API.")
    # Convert to DataFrame
    avg_house_prices_df = pd.DataFrame(avg_house_prices_data, columns=['Avg_House_Price'])
    avg_house_prices_df.index.name = 'Date'
    avg_house_prices_df.reset_index(inplace=True)
    # Add quarter column
    avg_house_prices_df['Quarter'] = avg_house_prices_df['Date'].dt.to_period('Q').dt.strftime('Q%q-%Y')

except Exception as e:
    print(f"Error fetching average house prices data: {e}")
    engine_status = 'Error'
    exit()

# Merge
house_prices_df = pd.merge(median_house_prices_df, avg_house_prices_df, on='Date', how='left')

# Resolve duplicate 'Quarter' columns
if 'Quarter_x' in house_prices_df.columns:
    house_prices_df['Quarter'] = house_prices_df['Quarter_x']
    house_prices_df.drop(columns=['Quarter_x', 'Quarter_y'], inplace=True)

try:
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    cur = conn.cursor()
except Exception as e:
    print(f"Error connecting to the database: {e}")
    engine_status = 'Error'
    exit()

current_timestamp = datetime.now()
insert_query = sql.SQL("""
    INSERT INTO house_prices (Date, median_house_price, avg_house_price, Quarter, when_updated)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (Date) DO UPDATE 
    SET median_house_price = EXCLUDED.median_house_price,
        avg_house_price = EXCLUDED.avg_house_price,
        Quarter = EXCLUDED.Quarter,
        when_updated = EXCLUDED.when_updated
""")
for index, row in house_prices_df.iterrows():
    cur.execute(insert_query, (row['Date'], row['Median_House_Price'], row['Avg_House_Price'], row['Quarter'], current_timestamp))
    
# Update the status of the 'house_prices' engine in the engines table
update_engine_query = sql.SQL("""
    UPDATE engines
    SET status = %s,
        last_checkin = %s
    WHERE engine = %s
""")
cur.execute(update_engine_query, (engine_status, current_timestamp, 'house_prices'))

conn.commit()

cur.close()
conn.close()
