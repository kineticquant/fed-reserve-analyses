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

try:
    fred = Fred(api_key=fredk)
    print("Successfully connected to FRED API client.")
except Exception as e:
    print(f"Error initializing Fred API client: {e}")
    engine_status = 'Error'
    exit()

try:
    gdp_data = fred.get_series('GFDEGDQ188S')
    gdp_df = pd.DataFrame(gdp_data, columns=['debt_gdp_percent'])
    gdp_df.index.name = 'date'
    gdp_df.reset_index(inplace=True)
except Exception as e:
    print(f"Error fetching GDP data: {e}")
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

president_query = """
    SELECT president_name, start_date, end_date
    FROM presidential_terms
"""

president_df = pd.read_sql(president_query, conn)

president_df['start_date'] = pd.to_datetime(president_df['start_date'])
president_df['end_date'] = pd.to_datetime(president_df['end_date'])

def get_president(date):
    date = pd.Timestamp(date)
    for _, row in president_df.iterrows():
        if row['start_date'] <= date <= row['end_date']:
            return row['president_name']
    return None

gdp_df['president'] = gdp_df['date'].apply(get_president)


def calculate_president_gdp_changes(df):
    for president in df['president'].unique():
        pres_df = df[df['president'] == president]
        
        if not pres_df.empty:
            start_date = pres_df['date'].min()
            end_date = pres_df['date'].max()

            if pd.notna(start_date) and pd.notna(end_date):
                start_value = pres_df[pres_df['date'] == start_date]['debt_gdp_percent'].values[0]
                end_value = pres_df[pres_df['date'] == end_date]['debt_gdp_percent'].values[0]

                total_percent_change = (end_value - start_value)

                df.loc[
                    (df['president'] == president) &
                    (df['date'] >= start_date) &
                    (df['date'] <= end_date),
                    'president_start_value'
                ] = start_value

                df.loc[
                    (df['president'] == president) &
                    (df['date'] >= start_date) &
                    (df['date'] <= end_date),
                    'president_end_value'
                ] = end_value

                df.loc[
                    (df['president'] == president) &
                    (df['date'] >= start_date) &
                    (df['date'] <= end_date),
                    'president_total_percent_change'
                ] = total_percent_change

calculate_president_gdp_changes(gdp_df)

insert_query = sql.SQL("""
    INSERT INTO federal_debt_gdp (date, debt_gdp_percent, president, president_start_value, president_end_value, president_total_percent_change, when_updated)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (date) DO UPDATE 
    SET debt_gdp_percent = EXCLUDED.debt_gdp_percent,
        president = EXCLUDED.president,
        president_start_value = EXCLUDED.president_start_value,
        president_end_value = EXCLUDED.president_end_value,
        president_total_percent_change = EXCLUDED.president_total_percent_change,
        when_updated = EXCLUDED.when_updated
""")
engine_status = 'Success'
current_timestamp = datetime.now()

for index, row in gdp_df.iterrows():
    cur.execute(insert_query, (
        row['date'], row['debt_gdp_percent'], row['president'], 
        row['president_start_value'], row['president_end_value'], 
        row['president_total_percent_change'], current_timestamp
    ))

update_engine_query = sql.SQL("""
    UPDATE engines
    SET status = %s,
        last_checkin = %s
    WHERE engine = %s
""")
cur.execute(update_engine_query, (engine_status, current_timestamp, 'federal_debt_gdp'))

conn.commit()

cur.close()
conn.close()

print("Data insertion and engine update completed successfully.")
