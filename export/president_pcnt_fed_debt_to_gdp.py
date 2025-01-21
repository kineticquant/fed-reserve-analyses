import psycopg2
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from decimal import Decimal

load_dotenv()

dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")

json_folder = os.getenv("JSON_FOLDER")

current_time = datetime.now()

conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
)

query = """
SELECT DISTINCT president, round(president_total_percent_change,3) as president_total_percent_change
FROM federal_debt_gdp
ORDER BY president_total_percent_change ASC;
"""

with conn.cursor() as cursor:
    cursor.execute(query)
    data = cursor.fetchall()

data_list = []
for row in data:
    data_dict = {
        "president": row[0],
        "percent_change": float(row[1]) if isinstance(row[1], Decimal) else row[1]
    }
    data_list.append(data_dict)

os.makedirs(json_folder, exist_ok=True)

json_file_path = os.path.join(json_folder, "federal_debt_gdp.json")

with open(json_file_path, "w") as json_file:
    json.dump(data_list, json_file, indent=4)

# Update the engine status
update_engine = """
    UPDATE engines
    SET last_checkin = %s,
    status = %s
    WHERE engine = %s
"""

with conn.cursor() as cursor:
    cursor.execute(update_engine, (current_time, 'Success', 'export_president_pcnt_fed_debt_to_gdp'))

conn.commit()
conn.close()
