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

# Query to get Biden's term dates
biden_term_query = """
    SELECT start_date, end_date
    FROM presidential_terms
    WHERE president_name = 'Joe Biden'
"""
try:
    biden_term_df = pd.read_sql_query(biden_term_query, conn)
    # Extract start and end dates
    biden_start_date = biden_term_df['start_date'].values[0]
    biden_end_date = biden_term_df['end_date'].values[0]
except Exception as e:
    print(f"Error fetching Biden's term dates: {e}")
    conn.close()
    exit()

# Query to get DJI data for Biden's term
dji_query = """
    SELECT Date, dji
    FROM dji
    WHERE Date BETWEEN %s AND %s
"""
try:
    with conn.cursor() as cur:
        cur.execute(dji_query, (biden_start_date, biden_end_date))
        dji_data = cur.fetchall()
    
    # Convert to DataFrame
    dji_df = pd.DataFrame(dji_data, columns=['Date', 'DJI'])
except Exception as e:
    print(f"Error fetching DJI data: {e}")
    conn.close()
    exit()

conn.close()

# Convert 'Date' column to datetime
dji_df['Date'] = pd.to_datetime(dji_df['Date'])

dji_df.sort_values('Date', inplace=True)

fig = go.Figure()

# Add DJI trace
fig.add_trace(go.Scatter(
    x=dji_df['Date'],
    y=dji_df['DJI'],
    mode='lines',
    name='DJI Index',
    line=dict(color='orange')
))

# Update layout for dark mode with additional styling
fig.update_layout(
    template='plotly_dark',
    xaxis_title='Date',
    yaxis_title='DJI',
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
    width=800,  # Set the width of the figure to fixed
    height=600  # Set the height of the figure to fixed
)

fig.show()
