import uuid
import psycopg2
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

db_config = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "dbname": os.getenv("POSTGRES_DB"),
}

new_id = str(uuid.uuid4())

from uuid import UUID

property_data = (
    new_id,  # UUID para la propiedad como string
    'Casa Moderna',
    'Moderna con jardín',
    'house',
    'sale',
    'CABA',
    'Calle Falsa 123',
    250000,
    'available',
    str(UUID('851dd10d-7f2a-4084-804f-f2d3a73eaa5e')),  # Convertido a string
    datetime.now(),
    datetime.now(),
    None,
    None
)



try:
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO properties (
            id, title, description, property_type, operation_type,
            location, address, price, status, user_id,
            created_at, updated_at, photos, geolocation
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
    """

    cursor.execute(insert_query, property_data)
    conn.commit()
    print(f"✅ Propiedad insertada con id: {new_id}")

except Exception as e:
    print(f"❌ Error al insertar propiedad: {e}")

finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
