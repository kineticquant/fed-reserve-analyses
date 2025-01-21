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
fred = os.getenv('FREDK')

engine_status = 'In Progress'

UNEMPLOYMENT_SERIES_ID = 'UNRATE'  # FRED series ID for unemployment rate

try:
    fred = Fred(api_key=fred)
    print("Successfully connected to FRED API client.")
    engine_status = 'Success'
except Exception as e:
    print(f"Error initializing Fred API client: {e}")
    engine_status = 'Error'
    exit()

try:
    unemployment_data = fred.get_series(UNEMPLOYMENT_SERIES_ID)
    print("Successfully fetched data from FRED API.")
    # Convert to DataFrame
    unemployment_df = pd.DataFrame(unemployment_data, columns=['Unemployment Rate'])
    unemployment_df.index.name = 'Date'
    unemployment_df.reset_index(inplace=True)
    engine_status = 'Success'

except Exception as e:
    print(f"Error fetching unemployment data: {e}")
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
    INSERT INTO unemployment_data (Date, Unemployment_Rate, when_updated)
    VALUES (%s, %s, %s)
    ON CONFLICT (Date) DO UPDATE 
    SET Unemployment_Rate = EXCLUDED.Unemployment_Rate,
        when_updated = EXCLUDED.when_updated
""")
for index, row in unemployment_df.iterrows():
    cur.execute(insert_query, (row['Date'], row['Unemployment Rate'], current_timestamp))
    
# Update the status of the 'unemployment' engine in the engines table
update_engine_query = sql.SQL("""
    UPDATE engines
    SET status = %s,
        last_checkin = %s
    WHERE engine = %s
""")
cur.execute(update_engine_query, (engine_status, current_timestamp, 'unemployment'))

conn.commit()

cur.close()
conn.close()