import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def run_sql_file(filename: str):
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, 'r') as f:
        sql = f.read()
    with psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB")
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        print(f"✅ Ejecutado: {filename}")

if __name__ == "__main__":
   
    run_sql_file("create_trigger_notify_property.sql")
