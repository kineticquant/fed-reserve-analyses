# Series is DJIA

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

DJI_SERIES_ID = 'DJIA'  # FRED series ID for Dow Jones Industrial Average

try:
    fred = Fred(api_key=fredk)
    print("Successfully connected to FRED API client.")
    engine_status = 'Success'
except Exception as e:
    print(f"Error initializing Fred API client: {e}")
    engine_status = 'Error'
    exit()

try:
    dji_data = fred.get_series(DJI_SERIES_ID)
    print("Successfully fetched data from FRED API.")
    
    # Convert to DataFrame
    dji_df = pd.DataFrame(dji_data, columns=['DJI'])
    dji_df.index.name = 'Date'
    dji_df.reset_index(inplace=True)
    
    # Drop rows where 'DJI' is NaN
    dji_df = dji_df.dropna(subset=['DJI'])
    
    # Add quarter column
    dji_df['Quarter'] = dji_df['Date'].dt.to_period('Q').dt.strftime('Q%q-%Y')
    engine_status = 'Success'
except Exception as e:
    print(f"Error fetching DJI data: {e}")
    engine_status = 'Error'
    exit()

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
    INSERT INTO dji (Date, DJI, Quarter, when_updated)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (Date) DO UPDATE 
    SET DJI = EXCLUDED.DJI,
        Quarter = EXCLUDED.Quarter,
        when_updated = EXCLUDED.when_updated
""")
for index, row in dji_df.iterrows():
    cur.execute(insert_query, (row['Date'], row['DJI'], row['Quarter'], current_timestamp))
    
# Update the status of the 'dji' engine in the engines table
update_engine_query = sql.SQL("""
    UPDATE engines
    SET status = %s,
        last_checkin = %s
    WHERE engine = %s
""")
cur.execute(update_engine_query, (engine_status, current_timestamp, 'dji'))

conn.commit()

cur.close()
conn.close()
