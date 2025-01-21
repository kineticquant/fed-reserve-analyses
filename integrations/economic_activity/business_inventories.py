# Total Business inventories (BUSINV)
# Total Business: Inventories to Sales Ratio (ISRATIO)
# Retailers: Inventories to Sales Ratio (RETAILIRSA)
# Manufacturers: Inventories to Sales Ratio (MNFCTRIRSA)
# Merchant Wholesalers: Inventories to Sales Ratio (WHLSLRIRSA)
# Auto Inventory to Sales Ratio (AISRSA)
# Total Business Sales (TOTBUSSMSA)
# Retailer Inventories (RETAILIMSA)

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

# Series IDs
series_dict = {
    'BUSINV': 'total_business_inventories',
    'ISRATIO': 'inventories_to_sales_ratio',
    'RETAILIRSA': 'retailers_inventories_to_sales_ratio',
    'MNFCTRIRSA': 'manufacturers_inventories_to_sales_ratio',
    'WHLSLRIRSA': 'wholesalers_inventories_to_sales_ratio',
    'AISRSA': 'auto_inventory_to_sales_ratio',
    'TOTBUSSMSA': 'total_business_sales',
    'RETAILIMSA': 'retailer_inventories'
}

# Initialize Fred API client
try:
    fred = Fred(api_key=fredk)
    print("Successfully connected to FRED API client.")
    engine_status = 'Success'
except Exception as e:
    print(f"Error initializing Fred API client: {e}")
    engine_status = 'Error'
    exit()

# Connect to PostgreSQL
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

for series_id, table_name in series_dict.items():
    try:
        # Fetch data from FRED API
        data = fred.get_series(series_id)
        print(f"Successfully fetched data for series {series_id} from FRED API.")
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=[table_name])
        df.index.name = 'Date'
        df.reset_index(inplace=True)
        
        # Add quarter column
        df['Quarter'] = df['Date'].dt.to_period('Q').dt.strftime('Q%q-%Y')

        # Insert data into table with merge (upsert)
        insert_query = sql.SQL(f"""
            INSERT INTO {table_name} (Date, {table_name}, Quarter, when_updated)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (Date) DO UPDATE 
            SET {table_name} = EXCLUDED.{table_name},
                Quarter = EXCLUDED.Quarter,
                when_updated = EXCLUDED.when_updated
        """)
        for index, row in df.iterrows():
            cur.execute(insert_query, (row['Date'], row[table_name], row['Quarter'], current_timestamp))
        
        print(f"Successfully inserted data into {table_name} table.")
    except Exception as e:
        print(f"Error processing series {series_id}: {e}")
        engine_status = 'Error'
        continue
    
# Update the status of the 'business_inventories' engine in the engines table
update_engine_query = sql.SQL("""
    UPDATE engines
    SET status = %s,
        last_checkin = %s
    WHERE engine = %s
""")
cur.execute(update_engine_query, (engine_status, current_timestamp, 'business_inventories'))

conn.commit()

cur.close()
conn.close()
