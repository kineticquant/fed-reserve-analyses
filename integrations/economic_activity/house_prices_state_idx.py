import pandas as pd
from fredapi import Fred
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
from datetime import datetime

#### This engine works with indexes and not base value. If I wanted to apply a base value (like 100,000$), then I need to define and calc that:
# base_value = 100000  # Example base value in dollars

# Calculate dollar amounts based on the index
# state_df['4_years_dollar'] = (state_df['4_years'] / 100) * base_value
# state_df['10_years_dollar'] = (state_df['10_years'] / 100) * base_value
# state_df['25_years_dollar'] = (state_df['25_years'] / 100) * base_value
# state_df['all_time_dollar'] = (state_df['all_time'] / 100) * base_value

load_dotenv()

dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
fredk = os.getenv('FREDK')

engine_status = 'In Progress'

states = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]

try:
    fred = Fred(api_key=fredk)
    print("Successfully connected to FRED API client.")
except Exception as e:
    print(f"Error initializing Fred API client: {e}")
    engine_status = 'Error'
    exit()

all_states_df = pd.DataFrame()

for state in states:
    series_id = f'{state}STHPI'
    try:
        state_data = fred.get_series(series_id)
        state_df = pd.DataFrame(state_data, columns=['House_Price'])
        state_df.index.name = 'Date'
        state_df['State'] = state
        state_df['Quarter'] = state_df.index.to_period('Q').strftime('Q%q-%Y')
        state_df.reset_index(inplace=True)
        

        state_df['4_years'] = state_df['House_Price'] - state_df['House_Price'].shift(4*4)  # Approx 4*4 quarters = 4 years
        state_df['4_years_percent'] = (state_df['4_years'] / state_df['House_Price'].shift(4*4)) * 100
        
        state_df['10_years'] = state_df['House_Price'] - state_df['House_Price'].shift(10*4)  # Approx 10*4 quarters = 10 years
        state_df['10_years_percent'] = (state_df['10_years'] / state_df['House_Price'].shift(10*4)) * 100
        
        state_df['25_years'] = state_df['House_Price'] - state_df['House_Price'].shift(25*4)  # Approx 25*4 quarters = 25 years
        state_df['25_years_percent'] = (state_df['25_years'] / state_df['House_Price'].shift(25*4)) * 100
        
        state_df['all_time'] = state_df['House_Price'] - state_df['House_Price'].iloc[0]  # Difference from first available value
        state_df['all_time_percent'] = (state_df['all_time'] / state_df['House_Price'].iloc[0]) * 100
        
        all_states_df = pd.concat([all_states_df, state_df])
    except Exception as e:
        print(f"Error fetching data for {state}: {e}")

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

all_states_df['president'] = all_states_df['Date'].apply(get_president)

def calculate_president_changes(df):
    for state in df['State'].unique():
        state_df = df[df['State'] == state]
        
        for president in state_df['president'].unique():
            pres_df = state_df[state_df['president'] == president]
            
            if not pres_df.empty:
                start_date = pres_df['Date'].min()
                end_date = pres_df['Date'].max()

                if pd.notna(start_date) and pd.notna(end_date):
                    start_price = pres_df[pres_df['Date'] == start_date]['House_Price'].values[0]
                    end_price = pres_df[pres_df['Date'] == end_date]['House_Price'].values[0]

                    amt_change = end_price - start_price
                    percent_change = (amt_change / start_price) * 100

                    df.loc[
                        (df['State'] == state) &
                        (df['president'] == president) &
                        (df['Date'] >= start_date) &
                        (df['Date'] <= end_date),
                        'president_amt'
                    ] = amt_change

                    df.loc[
                        (df['State'] == state) &
                        (df['president'] == president) &
                        (df['Date'] >= start_date) &
                        (df['Date'] <= end_date),
                        'president_percent'
                    ] = percent_change

calculate_president_changes(all_states_df)

insert_query = sql.SQL("""
    INSERT INTO state_house_prices (Date, State, House_Price, Quarter, "4_years", "4_years_percent", "10_years", "10_years_percent", "25_years", "25_years_percent", "all_time", "all_time_percent", president, president_amt, president_percent, when_updated)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (Date, State) DO UPDATE 
    SET House_Price = EXCLUDED.House_Price,
        Quarter = EXCLUDED.Quarter,
        "4_years" = EXCLUDED."4_years",
        "4_years_percent" = EXCLUDED."4_years_percent",
        "10_years" = EXCLUDED."10_years",
        "10_years_percent" = EXCLUDED."10_years_percent",
        "25_years" = EXCLUDED."25_years",
        "25_years_percent" = EXCLUDED."25_years_percent",
        "all_time" = EXCLUDED."all_time",
        "all_time_percent" = EXCLUDED."all_time_percent",
        president = EXCLUDED.president,
        president_amt = EXCLUDED.president_amt,
        president_percent = EXCLUDED.president_percent,
        when_updated = EXCLUDED.when_updated
""")
engine_status = 'Success'
current_timestamp = datetime.now()

for index, row in all_states_df.iterrows():
    cur.execute(insert_query, (
        row['Date'], row['State'], row['House_Price'], row['Quarter'], 
        row['4_years'], row['4_years_percent'],
        row['10_years'], row['10_years_percent'],
        row['25_years'], row['25_years_percent'],
        row['all_time'], row['all_time_percent'],
        row['president'],
        row['president_amt'],
        row['president_percent'],
        current_timestamp
    ))


update_engine_query = sql.SQL("""
    UPDATE engines
    SET status = %s,
        last_checkin = %s
    WHERE engine = %s
""")
cur.execute(update_engine_query, (engine_status, current_timestamp, 'house_state_idx'))

conn.commit()

cur.close()
conn.close()

print("Data insertion and engine update completed successfully.")
