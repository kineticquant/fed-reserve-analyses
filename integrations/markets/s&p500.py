# Series SP500

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

SP500_SERIES_ID = 'SP500'  # FRED series ID for S&P 500

try:
    fred = Fred(api_key=fredk)
    print("Successfully connected to FRED API client.")
    engine_status = 'Success'
except Exception as e:
    print(f"Error initializing Fred API client: {e}")
    engine_status = 'Error'
    exit()

try:
    sp500_data = fred.get_series(SP500_SERIES_ID)
    print("Successfully fetched data from FRED API.")
    
    sp500_df = pd.DataFrame(sp500_data, columns=['S&P 500'])
    sp500_df.index.name = 'Date'
    sp500_df.reset_index(inplace=True)
    
    sp500_df = sp500_df.dropna(subset=['S&P 500'])
    
    # Add quarter column
    sp500_df['Quarter'] = sp500_df['Date'].dt.to_period('Q').dt.strftime('Q%q-%Y')
    engine_status = 'Success'
except Exception as e:
    print(f"Error fetching S&P 500 data: {e}")
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
    INSERT INTO sp500 (Date, SP500, Quarter, when_updated)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (Date) DO UPDATE 
    SET SP500 = EXCLUDED.SP500,
        Quarter = EXCLUDED.Quarter,
        when_updated = EXCLUDED.when_updated
""")
for index, row in sp500_df.iterrows():
    cur.execute(insert_query, (row['Date'], row['S&P 500'], row['Quarter'], current_timestamp))
    
# Update the status of the 'sp500' engine in the engines table
update_engine_query = sql.SQL("""
    UPDATE engines
    SET status = %s,
        last_checkin = %s
    WHERE engine = %s
""")
cur.execute(update_engine_query, (engine_status, current_timestamp, 's&p500'))

conn.commit()

cur.close()
conn.close()
