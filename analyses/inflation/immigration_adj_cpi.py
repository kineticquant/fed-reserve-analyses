import os
from dotenv import load_dotenv
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

migration_query = """
SELECT year, number
FROM us_ill_migration
WHERE year BETWEEN 2014 AND 2024;
"""
migration_df = pd.read_sql(migration_query, conn)

cpi_query = """
SELECT date, cpi
FROM cpi
WHERE date >= '2014-01-01' AND date <= '2024-12-31';
"""
cpi_df = pd.read_sql(cpi_query, conn)

conn.close()

# Convert 'date' to datetime and extract year for CPI data
cpi_df['date'] = pd.to_datetime(cpi_df['date'])
cpi_df['year'] = cpi_df['date'].dt.year

# Aggregate CPI data by year
annual_cpi_df = cpi_df.groupby('year')['cpi'].mean().reset_index()

merged_df = pd.merge(migration_df, annual_cpi_df, on='year', how='left')

merged_df.sort_values('year', inplace=True)

fig, ax1 = plt.subplots(figsize=(14, 7))

ax1.set_xlabel('Year', fontsize=14)
ax1.set_ylabel('US Illegal Migration Population', fontsize=14, color='tab:blue')
ax1.plot(merged_df['year'], merged_df['number'], 'o-', color='tab:blue', label='US Illegal Migration Population')
ax1.tick_params(axis='y', labelcolor='tab:blue')

ax1.yaxis.set_ticks([])
ax1.yaxis.set_tick_params(labelsize=0)

ax2 = ax1.twinx()
ax2.set_ylabel('CPI', fontsize=14, color='tab:orange')
ax2.plot(merged_df['year'], merged_df['cpi'], 's-', color='tab:orange', label='CPI')
ax2.tick_params(axis='y', labelcolor='tab:orange')

ax2.yaxis.set_ticks([])
ax2.yaxis.set_tick_params(labelsize=0)

# Add watermark
fig.text(0.5, 0.5, 'MY WATERMARK REMOVED', fontsize=40, color='grey', alpha=0.1, ha='center', va='center')

# Title and legends
plt.title('US Undocumented Population and CPI (2014-2024)', fontsize=16)
fig.tight_layout()

plt.show()
