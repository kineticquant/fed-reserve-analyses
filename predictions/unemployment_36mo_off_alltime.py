import os
import pandas as pd
import psycopg2
import plotly.graph_objs as go
from statsmodels.tsa.arima.model import ARIMA
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    return conn

def fetch_unemployment_data():
    conn = get_db_connection()
    query = """
    SELECT date, unemployment_rate
    FROM unemployment_data
    ORDER BY date
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

df = fetch_unemployment_data()

# Fit ARIMA model
model = ARIMA(df['unemployment_rate'], order=(5, 1, 0))  # Adjust order as needed
model_fit = model.fit()

# Forecast next 36 months
forecast = model_fit.forecast(steps=36)
forecast_dates = pd.date_range(start=df['date'].iloc[-1], periods=37, freq='M')[1:]
forecast_df = pd.DataFrame({'date': forecast_dates, 'unemployment_rate': forecast})


# Concatenate historical and forecast data
full_df = pd.concat([df, forecast_df])

# Create the Plotly graph
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df['date'],
    y=df['unemployment_rate'],
    mode='lines',
    name='Historical Unemployment Rate',
    line=dict(color='lightblue')
))

fig.add_trace(go.Scatter(
    x=forecast_df['date'],
    y=forecast_df['unemployment_rate'],
    mode='lines',
    name='Forecast Unemployment Rate',
    line=dict(color='red', dash='dash')
))

fig.update_layout(
    template='plotly_dark',
    xaxis_title='Date',
    yaxis_title='Unemployment Rate',
    legend=dict(x=0, y=1),
    plot_bgcolor='#2c2c2c',
    paper_bgcolor='#2c2c2c',
    annotations=[
        dict(
            x=0.95,
            y=0.01,
            xref='paper',
            yref='paper',
            text='Forecast by Erie Analytica',
            showarrow=False,
            font=dict(color='white')
        )
    ],
    width=1600,  # Set the width of the figure
    height=1000  # Set the height of the figure
)

fig.show()
