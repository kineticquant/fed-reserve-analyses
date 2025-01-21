import pandas as pd
import requests
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
eia_api_key = os.getenv('EIA_API_KEY')

engine_status = 'In Progress'

# EIA API settings
#EIA_SERIES_ID = 'PET.MCRFPUS1.M'  # Series ID for US Monthly Crude Oil Production
EIA_SERIES_ID = 'MCRFPUS2'  # Series ID for US Monthly Crude Oil Production

# Fetch oil production data from EIA API
try:
    url = f'https://api.eia.gov/v2/petroleum/sum/snd/data/?frequency=monthly&data[0]=value&facets[series][]={EIA_SERIES_ID}&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000&api_key={eia_api_key}'
    response = requests.get(url)
    response.raise_for_status()  # Check if the request was successful
    data = response.json()
    
    # Print the entire JSON response to understand its structure
    #print("API Response:", data)
    
    # Extract monthly
    series_data = data.get('response', {}).get('data', [])
    
    if not series_data:
        raise ValueError("No data found in the API response.")
    
    oil_df = pd.DataFrame(series_data)
    oil_df['period'] = pd.to_datetime(oil_df['period'], format='%Y-%m')
    oil_df['value'] = pd.to_numeric(oil_df['value'], errors='coerce')
    
    # Rename columns for consistency
    oil_df.rename(columns={'period': 'Date', 'value': 'Production'}, inplace=True)
    
    # Drop rows where 'Production' is NaN
    oil_df = oil_df.dropna(subset=['Production'])
    
    print("Successfully fetched and processed data from EIA API.")
    engine_status = 'Success'
except Exception as e:
    print(f"Error fetching or processing data from EIA API: {e}")
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
    print("Successfully connected to the database.")
except Exception as e:
    print(f"Error connecting to the database: {e}")
    engine_status = 'Error'
    exit()

current_timestamp = datetime.now()

insert_query = sql.SQL("""
    INSERT INTO us_oil_production_monthly_mil_bar_pd  (Date, Production, when_updated)
    VALUES (%s, %s, %s)
    ON CONFLICT (Date) DO UPDATE 
    SET Production = EXCLUDED.Production,
        when_updated = EXCLUDED.when_updated
""")

for index, row in oil_df.iterrows():
    cur.execute(insert_query, (row['Date'], row['Production'], current_timestamp))

# Update the status of the 'us_oil_productio_by_monthn' engine in the engines table
update_engine_query = sql.SQL("""
    UPDATE engines
    SET status = %s,
        last_checkin = %s
    WHERE engine = %s
""")
cur.execute(update_engine_query, (engine_status, current_timestamp, 'us_oil_production_by_month'))

conn.commit()

cur.close()
conn.close()
