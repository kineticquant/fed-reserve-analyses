import os
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

start_date = '2000-01-01'
end_date = '2024-08-01'

oil_query = """
SELECT date, production
FROM us_oil_production_monthly_mil_bar_pd
WHERE date >= '2020-05-01'
ORDER BY date;
"""

cpi_query = """
SELECT date, inflation_rate
FROM cpi
WHERE date >= '2020-05-01'
ORDER BY date;
"""

oil_df = pd.read_sql(oil_query, conn)
cpi_df = pd.read_sql(cpi_query, conn)


conn.close()

merged_df = pd.merge(oil_df, cpi_df, on='date', how='outer')

merged_df['date'] = pd.to_datetime(merged_df['date'])

merged_df.set_index('date', inplace=True)

all_months = pd.date_range(start=start_date, end=end_date, freq='MS')

merged_df = merged_df.reindex(all_months)

merged_df.fillna(method='ffill', inplace=True)

fig, ax1 = plt.subplots(figsize=(14, 8))

ax1.plot(merged_df.index, merged_df['production'], label='Oil Production (Million Barrels per Day)', color='blue')
ax1.set_xlabel('Date')
ax1.set_ylabel('Oil Production (Million Barrels per Day)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

# Create a secondary y-axis for inflation rate
ax2 = ax1.twinx()
ax2.plot(merged_df.index, merged_df['inflation_rate'], label='Inflation Rate (%)', color='red')
ax2.set_ylabel('Inflation Rate (%)', color='red')
ax2.tick_params(axis='y', labelcolor='red')

# Customize the plot
plt.title('US Oil Production vs. Inflation Rate ('+start_date+' to '+end_date+')')
plt.grid(True)

# Rotate date labels for better readability
plt.xticks(rotation=45)

plt.show()
