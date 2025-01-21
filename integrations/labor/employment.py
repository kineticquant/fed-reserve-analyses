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

FULL_TIME_SERIES_ID = 'LNS12500000' 
PART_TIME_SERIES_ID = 'LNS12600000' 

engine_status = 'In Progress'

# Initialize Fred API client
try:
    fred = Fred(api_key=fredk)
    print("Successfully connected to FRED API client.")
    engine_status = 'Success'
except Exception as e:
    print(f"Error initializing Fred API client: {e}")
    engine_status = 'Error'
    exit()

# Fetch full-time job data
try:
    full_time_data = fred.get_series(FULL_TIME_SERIES_ID)
    print("Successfully fetched full-time job data.")
    full_time_df = pd.DataFrame(full_time_data, columns=['Job_Count'])
    full_time_df['Job_Count'] *= 1000  # Scale job counts
    engine_status = 'Success'
    full_time_df.index.name = 'Date'
    full_time_df.reset_index(inplace=True)
    full_time_df['Job_Type'] = 'full_time'
except Exception as e:
    print(f"Error fetching full-time job data: {e}")
    engine_status = 'Error'
    exit()

# Fetch part-time job data
try:
    part_time_data = fred.get_series(PART_TIME_SERIES_ID)
    print("Successfully fetched part-time job data.")
    part_time_df = pd.DataFrame(part_time_data, columns=['Job_Count'])
    part_time_df['Job_Count'] *= 1000  # Scale job counts
    engine_status = 'Success'
    part_time_df.index.name = 'Date'
    part_time_df.reset_index(inplace=True)
    part_time_df['Job_Type'] = 'part_time'
except Exception as e:
    print(f"Error fetching part-time job data: {e}")
    engine_status = 'Error'
    exit()

# Combine full-time and part-time job data
combined_df = pd.concat([full_time_df, part_time_df])

# Calculate monthly difference
combined_df['monthly_difference'] = combined_df.groupby('Job_Type')['Job_Count'].diff().fillna(0)

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
    INSERT INTO employment_jobs (Date, Job_Type, Job_Count, monthly_difference, when_updated)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (Date, Job_Type) DO UPDATE 
    SET Job_Count = EXCLUDED.Job_Count,
        monthly_difference = EXCLUDED.monthly_difference,
        when_updated = EXCLUDED.when_updated
""")
for index, row in combined_df.iterrows():
    cur.execute(insert_query, (row['Date'], row['Job_Type'], row['Job_Count'], row['monthly_difference'], current_timestamp))

# Update the status of the 'employment' engine in the engines table
engine_status = 'Success'
update_engine_query = sql.SQL("""
    UPDATE engines
    SET status = %s,
        last_checkin = %s
    WHERE engine = %s
""")
cur.execute(update_engine_query, (engine_status, current_timestamp, 'employment'))

conn.commit()

cur.close()
conn.close()

print("Full-time and part-time job data saved and merged successfully.")
