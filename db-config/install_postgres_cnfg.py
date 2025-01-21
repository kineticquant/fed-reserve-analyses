import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

#dotenv_path = '/path/to/your/.env'
#load_dotenv(dotenv_path=dotenv_path)

dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
environment_name = os.getenv("ENVIRONMENT_NAME")

conn = psycopg2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port
)

cursor = conn.cursor()

cursor.execute("SELECT * FROM SYS_CONF")

rows = cursor.fetchall()
if not rows:
    print("No rows found. Inserting installation values.")
    
    insert_SYS_CONF = """
    INSERT INTO SYS_CONF (IS_ALIVE, APP_ENV_NAME)
    VALUES (%s, %s)
    """
    values = ('Y', environment_name)
    
    cursor.execute(insert_SYS_CONF, values)
    
    conn.commit()

else:
    print("System Configuration rows found:")
    for row in rows:
        print(row)
        
### Moving to engine and table setup

### Ending engine and table setup 


cursor.close()
conn.close()

