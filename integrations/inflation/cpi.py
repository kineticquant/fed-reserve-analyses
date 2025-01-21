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

CPI_SERIES_ID = 'CPIAUCNS'  # FRED series ID for Consumer Price Index

try:
    fred = Fred(api_key=fredk)
    print("Successfully connected to FRED API client.")
    engine_status = 'Success'
except Exception as e:
    print(f"Error initializing Fred API client: {e}")
    engine_status = 'Error'
    exit()

try:
    cpi_data = fred.get_series(CPI_SERIES_ID)
    print("Successfully fetched data from FRED API.")
    
    # Convert to DataFrame
    cpi_df = pd.DataFrame(cpi_data, columns=['CPI'])
    cpi_df.index.name = 'Date'
    cpi_df.reset_index(inplace=True)
    
    # Ensure date column is datetime
    cpi_df['Date'] = pd.to_datetime(cpi_df['Date'])
    
    # Drop rows where 'CPI' is NaN
    cpi_df = cpi_df.dropna(subset=['CPI'])
    
    # Calculate Annual Inflation Rate as percentage
    cpi_df['Year'] = cpi_df['Date'].dt.year
    cpi_df['Month'] = cpi_df['Date'].dt.month
    
    cpi_df = cpi_df.sort_values(by=['Date'])
    
    # Shift CPI values by 12 months to calculate annual inflation
    cpi_df['CPI_Previous_Year'] = cpi_df['CPI'].shift(12)
    
    # Calculate Inflation Rate as percentage
    cpi_df['Inflation_Rate'] = (cpi_df['CPI'] - cpi_df['CPI_Previous_Year']) / cpi_df['CPI_Previous_Year'] * 100
    
    # Drop rows where 'Inflation_Rate' is NaN (first 12 months after shift)
    cpi_df = cpi_df.dropna(subset=['Inflation_Rate'])
    
    # Print first few rows to verify
    #print(cpi_df.head())

    # Add quarter column
    cpi_df['Quarter'] = cpi_df['Date'].dt.to_period('Q').dt.strftime('Q%q-%Y')
    engine_status = 'Success'
except Exception as e:
    print(f"Error fetching CPI data: {e}")
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
    INSERT INTO cpi (Date, CPI, Inflation_Rate, Quarter, when_updated)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (Date) DO UPDATE 
    SET CPI = EXCLUDED.CPI,
        Inflation_Rate = EXCLUDED.Inflation_Rate,
        Quarter = EXCLUDED.Quarter,
        when_updated = EXCLUDED.when_updated
""")
for index, row in cpi_df.iterrows():
    cur.execute(insert_query, (row['Date'], row['CPI'], row['Inflation_Rate'], row['Quarter'], current_timestamp))
    
# Update the status of the 'cpi' engine in the engines table
update_engine_query = sql.SQL("""
    UPDATE engines
    SET status = %s,
        last_checkin = %s
    WHERE engine = %s
""")
cur.execute(update_engine_query, (engine_status, current_timestamp, 'cpi'))

conn.commit()

cur.close()
conn.close()
