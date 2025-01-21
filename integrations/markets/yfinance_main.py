import pandas as pd
import yfinance as yf
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
from datetime import datetime
import time

load_dotenv()

dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")

engine_status = 'In Progress'

# Tickers and their labels
tickers = {
    'VIX': '^VIX',
    'DJI': '^DJI',
    'S&P': '^GSPC',
    'Nasdaq': '^IXIC',
    'Russell 2k': '^RUT',
    'SPY': 'SPY',
    'QQQ': 'QQQ',
    'BTC': 'BTC-USD',
    'ETH': 'ETH-USD',
    'US OIL': 'CL=F',
    'Gold': 'GC=F'
}

def fetch_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='2y')  # Fetch the last 2 years of data for various thresholds
        if len(hist) < 2:
            return None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None

        # Convert index to timezone-naive datetime
        hist.index = hist.index.tz_localize(None)
        
        # Get the most recent data
        today = hist.iloc[-1]
        current_price = today['Close']
        
        # Calculate the start of the current year for YTD
        start_of_year = datetime(datetime.now().year, 1, 1)
        
        thresholds = {
            '1w': pd.DateOffset(weeks=1),
            '1m': pd.DateOffset(months=1),
            '3m': pd.DateOffset(months=3),
            '6m': pd.DateOffset(months=6),
            '1y': pd.DateOffset(years=1),
            '18m': pd.DateOffset(months=18),
            '2y': pd.DateOffset(years=2),
            'ytd': start_of_year
        }
        
        changes = {}
        for key, offset in thresholds.items():
            if key == 'ytd':
                date_threshold = start_of_year
            else:
                date_threshold = datetime.now() - offset
            
            threshold_data = hist[hist.index >= date_threshold]
            if not threshold_data.empty:
                threshold_close = threshold_data.iloc[0]['Close']
                change = current_price - threshold_close
                change_pct = (change / threshold_close) * 100
                changes[f'{key}_price'] = f"{change:.2f}"
                changes[f'{key}_pct'] = f"{change_pct:.2f}%"
            else:
                changes[f'{key}_price'] = 'N/A'
                changes[f'{key}_pct'] = 'N/A'
        
        # Calculate daily change and percentage change
        yesterday = hist.iloc[-2]
        previous_close = yesterday['Close']
        change = current_price - previous_close
        change_pct = (change / previous_close) * 100
        
        return (current_price, 
                f"{change:.2f}", 
                f"{change_pct:.2f}%", 
                changes['1w_price'], 
                changes['1w_pct'], 
                changes['1m_price'], 
                changes['1m_pct'], 
                changes['3m_price'], 
                changes['3m_pct'], 
                changes['6m_price'], 
                changes['6m_pct'], 
                changes['1y_price'], 
                changes['1y_pct'], 
                changes['18m_price'], 
                changes['18m_pct'], 
                changes['2y_price'], 
                changes['2y_pct'], 
                changes['ytd_price'], 
                changes['ytd_pct'])
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None


def update_database():
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
        return 'Error'

    current_timestamp = datetime.now()

    insert_query = sql.SQL("""
    INSERT INTO app_home_page (TICKER, LAST, CHG, CHG_PCT, 
                               "1W_PRICE", "1W_PCT",
                               "1M_PRICE", "1M_PCT", 
                               "3M_PRICE", "3M_PCT", 
                               "6M_PRICE", "6M_PCT", 
                               "1Y_PRICE", "1Y_PCT", 
                               "18M_PRICE", "18M_PCT", 
                               "2Y_PRICE", "2Y_PCT", 
                               "YTD_PRICE", "YTD_PCT",
                               VISIBLE_YN)
    VALUES (%s, %s, %s, %s, 
            %s, %s,
            %s, %s, 
            %s, %s, 
            %s, %s, 
            %s, %s, 
            %s, %s, 
            %s, %s, 
            %s, %s, %s)
    ON CONFLICT (TICKER) DO UPDATE 
    SET LAST = EXCLUDED.LAST,
        CHG = EXCLUDED.CHG,
        CHG_PCT = EXCLUDED.CHG_PCT,
        "1W_PRICE" = EXCLUDED."1W_PRICE",
        "1W_PCT" = EXCLUDED."1W_PCT",
        "1M_PRICE" = EXCLUDED."1M_PRICE",
        "1M_PCT" = EXCLUDED."1M_PCT",
        "3M_PRICE" = EXCLUDED."3M_PRICE",
        "3M_PCT" = EXCLUDED."3M_PCT",
        "6M_PRICE" = EXCLUDED."6M_PRICE",
        "6M_PCT" = EXCLUDED."6M_PCT",
        "1Y_PRICE" = EXCLUDED."1Y_PRICE",
        "1Y_PCT" = EXCLUDED."1Y_PCT",
        "18M_PRICE" = EXCLUDED."18M_PRICE",
        "18M_PCT" = EXCLUDED."18M_PCT",
        "2Y_PRICE" = EXCLUDED."2Y_PRICE",
        "2Y_PCT" = EXCLUDED."2Y_PCT",
        "YTD_PRICE" = EXCLUDED."YTD_PRICE",
        "YTD_PCT" = EXCLUDED."YTD_PCT",
        VISIBLE_YN = EXCLUDED.VISIBLE_YN
""")

    

    for label, ticker in tickers.items():
        data = fetch_data(ticker)
        # Ensure the number of values matches the number of placeholders
        if data[0] is not None:
            cur.execute(insert_query, (label, *data, 'Y'))
            engine_status = 'Success'
        else:
            cur.execute(insert_query, (label, *['N/A'] * 18, 'N'))
            engine_status = 'Error'

    # Update the status of the 'yfinance_main' engine in the engines table
    update_engine_query = sql.SQL("""
        UPDATE engines
        SET status = %s,
            last_checkin = %s
        WHERE engine = %s
    """)
    cur.execute(update_engine_query, (engine_status, current_timestamp, 'yfinance_main'))
    print('Engine iteration complete.')

    # Commit and close
    conn.commit()
    cur.close()
    conn.close()
    
    return engine_status

# Run the script in a loop
#while True:
#    status = update_database()
#    if status == 'Error':
#        print("An error occurred. The script will retry.")
#    time.sleep(2)  # Pause execution for 2 seconds


# Run the script once
if __name__ == "__main__":
    status = update_database()
    print(f"Script execution completed. Status: {status}")