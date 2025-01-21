import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(filename='initEngine.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

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
    cur = conn.cursor()
    print("Successfully connected to the database.")
except Exception as e:
    error_message = f"Error connecting to the database: {e}"
    print(error_message)
    logging.error(error_message)
    exit()

# Get the current timestamp
current_time = datetime.now()

# Set the init to success / last checkin right away so no interval is shown
# If interval exists for init, we have a problem
update_init = sql.SQL("""
    UPDATE engines
    SET last_checkin = %s,
    status = %s
    WHERE engine = %s
""")

cur.execute(update_init, (current_time, 'Success', 'initEngine'))
if cur.rowcount == 0:
    logging.error("Failed to update initEngine status: No rows affected")
else:
    logging.info(f"Successfully updated initEngine status. Rows affected: {cur.rowcount}")

# Retrieve all rows from the engines table
select_query = sql.SQL("SELECT engine, last_checkin FROM engines")
cur.execute(select_query)
rows = cur.fetchall()

# Calculate time since last run and update the table
update_query = sql.SQL("""
    UPDATE engines
    SET time_since_last_run = %s
    WHERE engine = %s
""")

for row in rows:
    engine, last_checkin = row
    # Calculate the time difference
    if last_checkin:
        time_since_last_run = current_time - last_checkin
    else:
        time_since_last_run = None
    
    # Update the time_since_last_run column
    cur.execute(update_query, (time_since_last_run, engine))

# Commit the changes and close the connection
conn.commit()
cur.close()
conn.close()