import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM properties;")
    count = cursor.fetchone()[0]
    print(f"✅ Conectado a PostgreSQL. Hay {count} propiedades en la tabla.")
    cursor.close()
    conn.close()
except Exception as e:
    print("❌ Error conectando a PostgreSQL:", e)
