import pandas as pd
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
import plotly.graph_objects as go

load_dotenv()

dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")

try:
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    print("Successfully connected to the database.")
except Exception as e:
    print(f"Error connecting to the database: {e}")
    exit()

# Query to get Trump's term dates
trump_term_query = """
    SELECT start_date, end_date
    FROM presidential_terms
    WHERE president_name = 'Donald Trump'
"""
try:
    trump_term_df = pd.read_sql_query(trump_term_query, conn)
    # Extract start and end dates
    trump_start_date = trump_term_df['start_date'].values[0]
    trump_end_date = trump_term_df['end_date'].values[0]
except Exception as e:
    print(f"Error fetching Trump's term dates: {e}")
    conn.close()
    exit()

# Query to get S&P 500 data for Trump's term
sp500_query = """
    SELECT Date, sp500
    FROM sp500
    WHERE Date BETWEEN %s AND %s
"""
try:
    with conn.cursor() as cur:
        cur.execute(sp500_query, (trump_start_date, trump_end_date))
        sp500_data = cur.fetchall()
    
    sp500_df = pd.DataFrame(sp500_data, columns=['Date', 'S&P 500'])
except Exception as e:
    print(f"Error fetching S&P 500 data: {e}")
    conn.close()
    exit()

conn.close()

sp500_df['Date'] = pd.to_datetime(sp500_df['Date'])

sp500_df.sort_values('Date', inplace=True)

fig = go.Figure()

# Add S&P 500 trace
fig.add_trace(go.Scatter(
    x=sp500_df['Date'],
    y=sp500_df['S&P 500'],
    mode='lines',
    name='S&P 500 Index',
    line=dict(color='cyan')
))

# Update layout for dark mode with additional styling
fig.update_layout(
    template='plotly_dark',
    xaxis_title='Date',
    yaxis_title='S&P 500',
    legend=dict(x=0, y=1),
    plot_bgcolor='#2c2c2c',
    paper_bgcolor='#2c2c2c',
    annotations=[
        dict(
            x=0.95,
            y=0.01,
            xref='paper',
            yref='paper',
            text='Data by Erie Analytica',
            showarrow=False,
            font=dict(color='white')
        )
    ],
    width=800,  # Set the width of the figure
    height=600  # Set the height of the figure
)

fig.show()
