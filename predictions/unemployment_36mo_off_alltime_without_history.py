import os
import pandas as pd
import psycopg2
import plotly.graph_objs as go
from statsmodels.tsa.arima.model import ARIMA
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
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
    WHERE date >= CURRENT_DATE - INTERVAL '4 years'
    ORDER BY date
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

df = fetch_unemployment_data()

# Prepare the data for ML model
def prepare_data(df):
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year

    # Create lag features
    for lag in range(1, 13):
        df[f'lag_{lag}'] = df['unemployment_rate'].shift(lag)

    df = df.dropna().reset_index(drop=True)
    return df

# ARIMA model forecasting
def arima_forecast(df, periods=36):
    model = ARIMA(df['unemployment_rate'], order=(5, 1, 0))  # Adjust order as needed
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=periods)
    forecast_dates = pd.date_range(start=df['date'].iloc[-1], periods=periods + 1, freq='M')[1:]
    forecast_df = pd.DataFrame({'date': forecast_dates, 'unemployment_rate': forecast})
    return forecast_df

# RandomForest forecasting
# def random_forest_forecast(df, periods=36):
#     df_prepared = prepare_data(df)
#     X = df_prepared.drop(columns=['date', 'unemployment_rate'])
#     y = df_prepared['unemployment_rate']
    
#     model = RandomForestRegressor(n_estimators=100, random_state=42)
#     model.fit(X, y)

#     last_known_data = df_prepared.iloc[-1][X.columns].values.reshape(1, -1)
#     forecasts = []

#     for _ in range(periods):
#         pred = model.predict(last_known_data)[0]
#         forecasts.append(pred)
#         last_known_data = pd.DataFrame(last_known_data, columns=X.columns)
#         last_known_data = last_known_data.shift(-1, axis=1)
#         last_known_data.iloc[:, -1] = pred
#         last_known_data = last_known_data.values

#     forecast_dates = pd.date_range(start=df['date'].iloc[-1], periods=periods + 1, freq='M')[1:]
#     forecast_df = pd.DataFrame({'date': forecast_dates, 'unemployment_rate': forecasts})
#     return forecast_df

# Generate forecasts
arima_forecast_df = arima_forecast(df, periods=36)
# rf_forecast_df = random_forest_forecast(df, periods=36)

# Create the Plotly graph for ARIMA forecast
fig_arima = go.Figure()
fig_arima.add_trace(go.Scatter(
    x=arima_forecast_df['date'],
    y=arima_forecast_df['unemployment_rate'],
    mode='lines',
    name='ARIMA Forecast',
    line=dict(color='lightblue')
))
fig_arima.update_layout(
    title='Time Series Forecast of Unemployment Rate',
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
            text='Prediction by Erie Analytica',
            showarrow=False,
            font=dict(color='white')
        )
    ],
    width=800,  # Set the width of the figure
    height=600  # Set the height of the figure
)

# Create the Plotly graph for Random Forest forecast
# fig_rf = go.Figure()
# fig_rf.add_trace(go.Scatter(
#     x=rf_forecast_df['date'],
#     y=rf_forecast_df['unemployment_rate'],
#     mode='lines',
#     name='Random Forest Forecast',
#     line=dict(color='red')
# ))
# fig_rf.update_layout(
#     title='ML Forecast of Unemployment Rate',
#     template='plotly_dark',
#     xaxis_title='Date',
#     yaxis_title='Unemployment Rate',
#     legend=dict(x=0, y=1),
#     plot_bgcolor='#2c2c2c',
#     paper_bgcolor='#2c2c2c',
#     annotations=[
#         dict(
#             x=0.95,
#             y=0.01,
#             xref='paper',
#             yref='paper',
#             text='Prediction by Erie Analytica',
#             showarrow=False,
#             font=dict(color='white')
#         )
#     ],
#     width=800,  # Set the width of the figure
#     height=600  # Set the height of the figure
# )

fig_arima.show()
#fig_rf.show()
