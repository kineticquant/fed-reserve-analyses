# Gross Domestic Product (GDP)
# Gross National Product (GNP)
# Real Gross Domestic Product (GDPC1) 
#   Real gross domestic product is the inflation adjusted value of the goods and services produced by labor and property located in the United States.For more information see the Guide to the National Income and Product Accounts of the United States (NIPA).
# GDP Per Capita (A939RC0Q052SBEA)
#   Average economic output per person
# Real GDP Per Capita (A939RX0Q048SBEA)
#   Adjusts for inflation (more accurate reflection of economic size and change over time) - Economic change relative to inflation with GDP per person
# Generate Real GDP Growth Rate (per quarter and per year)


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

series_dict = {
    'GDP': 'gross_domestic_product',
    'GNP': 'gross_national_product',
    'GDPC1': 'real_gross_domestic_product',
    'A939RC0Q052SBEA': 'gdp_per_capita',
    'A939RX0Q048SBEA': 'real_gdp_per_capita'
}

try:
    fred = Fred(api_key=fredk)
    print("Successfully connected to FRED API client.")
    engine_status = 'Success'
except Exception as e:
    print(f"Error initializing Fred API client: {e}")
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

for series_id, table_name in series_dict.items():
    try:
        data = fred.get_series(series_id)
        print(f"Successfully fetched data for series {series_id} from FRED API.")

        df = pd.DataFrame(data, columns=[table_name])
        df.index.name = 'Date'
        df.reset_index(inplace=True)
        

        if table_name in ['gross_domestic_product', 'gross_national_product', 'real_gross_domestic_product']:
            df[table_name] = df[table_name] * 1e6  # Convert from billions to base unit
 
        df.dropna(inplace=True)
        
   
        df['Quarter'] = df['Date'].dt.to_period('Q').dt.strftime('Q%q-%Y')
        df['Year'] = df['Date'].dt.year

     
        insert_query = sql.SQL(f"""
            INSERT INTO {table_name} (Date, {table_name}, Quarter, Year, when_updated)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (Date) DO UPDATE 
            SET {table_name} = EXCLUDED.{table_name},
                Quarter = EXCLUDED.Quarter,
                Year = EXCLUDED.Year,
                when_updated = EXCLUDED.when_updated
        """)
        for index, row in df.iterrows():
            cur.execute(insert_query, (row['Date'], row[table_name], row['Quarter'], row['Year'], current_timestamp))
        
        print(f"Successfully inserted data into {table_name} table.")
    except Exception as e:
        print(f"Error processing series {series_id}: {e}")
        engine_status = 'Error'
        continue

try:
    cur.execute("""
        SELECT Date, real_gross_domestic_product FROM real_gross_domestic_product
        ORDER BY Date
    """)
    real_gdp_data = cur.fetchall()
    
    real_gdp_df = pd.DataFrame(real_gdp_data, columns=['Date', 'Real_GDP'])
    
    real_gdp_df['Date'] = pd.to_datetime(real_gdp_df['Date'])

    real_gdp_df['Real_GDP_Growth_Quarterly'] = real_gdp_df['Real_GDP'].pct_change() * 100
    real_gdp_df['Year'] = real_gdp_df['Date'].dt.year
    real_gdp_df['Real_GDP_Growth_Annual'] = real_gdp_df.groupby('Year')['Real_GDP'].pct_change() * 100


    real_gdp_df.dropna(inplace=True)

    insert_growth_query = """
        INSERT INTO real_gdp_growth (Date, Real_GDP_Growth_Quarterly, Real_GDP_Growth_Annual, when_updated)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (Date) DO UPDATE
        SET Real_GDP_Growth_Quarterly = EXCLUDED.Real_GDP_Growth_Quarterly,
            Real_GDP_Growth_Annual = EXCLUDED.Real_GDP_Growth_Annual,
            when_updated = EXCLUDED.when_updated
    """
    
    for index, row in real_gdp_df.iterrows():
        # Use Quarterly Only - Not Including Annual Anymore - 8.4.2024
        cur.execute(insert_growth_query, (row['Date'], row['Real_GDP_Growth_Quarterly'], 0, current_timestamp))
        #cur.execute(insert_growth_query, (row['Date'], row['Real_GDP_Growth_Quarterly'], row['Real_GDP_Growth_Annual'], current_timestamp))
    
    print("Successfully calculated and inserted real GDP growth rates.")
except Exception as e:
    print(f"Error calculating real GDP growth rates: {e}")
    engine_status = 'Error'

# Update the status of the 'gdp' engine in the engines table
update_engine_query = sql.SQL("""
    UPDATE engines
    SET status = %s,
        last_checkin = %s
    WHERE engine = %s
""")
cur.execute(update_engine_query, (engine_status, current_timestamp, 'gdp'))

conn.commit()

cur.close()
conn.close()
