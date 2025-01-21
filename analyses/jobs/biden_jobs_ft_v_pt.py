import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
import plotly.graph_objs as go
import plotly.offline as pyo

load_dotenv()

db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

conn = psycopg2.connect(
    dbname=db_name,
    user=db_user,
    password=db_password,
    host=db_host,
    port=db_port
)

# TODO: Update this to end date now that Trump is POTUS 47
query = """
    SELECT date, job_type, job_count
    FROM employment_jobs
    WHERE date >= '2021-02-01'
    AND date <= CURRENT_DATE
    ORDER BY date;
"""

df = pd.read_sql_query(query, conn)

conn.close()

df_pivot = df.pivot(index='date', columns='job_type', values='job_count').reset_index()

df_pivot.fillna(0, inplace=True)

trace_full_time = go.Scatter(
    x=df_pivot['date'],
    y=df_pivot['full_time'],
    mode='lines',
    name='Full Time Jobs',
    yaxis='y1'
)

trace_part_time = go.Scatter(
    x=df_pivot['date'],
    y=df_pivot['part_time'],
    mode='lines',
    name='Part Time Jobs',
    yaxis='y2'
)

layout = go.Layout(
    title='Job Count Over Time',
    xaxis=dict(title='Date'),
    yaxis=dict(
        title='Full Time Jobs',
        titlefont=dict(color='blue'),
        tickfont=dict(color='blue')
    ),
    yaxis2=dict(
        title='Part Time Jobs',
        titlefont=dict(color='red'),
        tickfont=dict(color='red'),
        overlaying='y',
        side='right'
    ),
    legend=dict(x=0, y=1),
)

fig = go.Figure(data=[trace_full_time, trace_part_time], layout=layout)

pyo.plot(fig)
