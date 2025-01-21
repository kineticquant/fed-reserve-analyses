import requests
import pandas as pd
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")

engine_status = 'In Progress'

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

try:
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": "false"
    }
    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame(data)

    volume_average = df['total_volume'].mean()
    total_volume_sum = df['total_volume'].sum()
    volume_trending_up = bool(df['total_volume'].pct_change().apply(lambda x: True if x > 0 else False).iloc[-1])
    total_in_volume_sum = df.apply(lambda x: x['total_volume'] if x['price_change_percentage_24h'] > 0 else 0, axis=1).sum()
    total_out_volume_sum = df.apply(lambda x: x['total_volume'] if x['price_change_percentage_24h'] < 0 else 0, axis=1).sum()

    insert_query = """
        INSERT INTO coin_volume_data 
(coin_id, name, symbol, market_cap, total_volume, in_volume, out_volume, volume_average, total_volume_sum, total_in_volume_sum, total_out_volume_sum, volume_trending_up, timestamp)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (coin_id) DO UPDATE
SET name = EXCLUDED.name,
    symbol = EXCLUDED.symbol,
    market_cap = EXCLUDED.market_cap,
    total_volume = EXCLUDED.total_volume,
    in_volume = EXCLUDED.in_volume,
    out_volume = EXCLUDED.out_volume,
    volume_average = EXCLUDED.volume_average,
    total_volume_sum = EXCLUDED.total_volume_sum,
    total_in_volume_sum = EXCLUDED.total_in_volume_sum,
    total_out_volume_sum = EXCLUDED.total_out_volume_sum,
    volume_trending_up = EXCLUDED.volume_trending_up,
    timestamp = EXCLUDED.timestamp;

    """

    for _, row in df.iterrows():
        cur.execute(insert_query, (
            row['id'],
            row['name'],
            row['symbol'],
            row['market_cap'],
            row['total_volume'],
            row['total_volume'] if row['price_change_percentage_24h'] > 0 else 0,
            row['total_volume'] if row['price_change_percentage_24h'] < 0 else 0,
            volume_average,
            total_volume_sum,
            total_in_volume_sum,
            total_out_volume_sum,
            volume_trending_up,  # Ensure this is a standard Python boolean
            current_timestamp
        ))

    conn.commit()
    print("Successfully inserted data into the coin_volume_data table.")
    engine_status = 'Success'

except Exception as e:
    print(f"Error fetching or processing CoinGecko data: {e}")
    engine_status = 'Error'

# Update the status of the 'crypto' engine in the engines table
try:
    update_engine_query = """
        UPDATE engines
        SET status = %s,
            last_checkin = %s
        WHERE engine = %s
    """
    cur.execute(update_engine_query, (engine_status, current_timestamp, 'coingather'))
    conn.commit()

except Exception as e:
    print(f"Error updating engine status: {e}")
    engine_status = 'Error'

finally:
    cur.close()
    conn.close()
