import os
import psycopg2
from dotenv import load_dotenv
from app.services.embeddings.opensearch_service import client
from bedrock_service import embed_text

load_dotenv()

# PostgreSQL connection
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    database=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)

cursor = conn.cursor()

# OpenSearch config
INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "properties")

# Crear índice si no existe
if not client.indices.exists(INDEX_NAME):
    client.indices.create(INDEX_NAME, body={
        "mappings": {
            "properties": {
                "text": {"type": "text"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 1536  # Ajusta según el modelo Bedrock
                }
            }
        }
    })

# Extraer propiedades desde PostgreSQL
cursor.execute("""
    SELECT title, description, property_type, address, operation_type
    FROM properties
""")

rows = cursor.fetchall()

for row in rows:
    title, description, ptype, address, op = row
    text = f"{title} - {description} - {ptype} - {address} - {op}"
    embedding = embed_text(text)

    doc = {
        "text": text,
        "embedding": embedding
    }
    client.index(index=INDEX_NAME, body=doc)

print("✅ Propiedades indexadas en OpenSearch")

cursor.close()
conn.close()

# Extraído de load_embeddings.py:
def create_index_if_not_exists():
    if not client.indices.exists(INDEX_NAME):
        client.indices.create(
            INDEX_NAME,
            body={
                "mappings": {
                    "properties": {
                        "text": {"type": "text"},
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 1536
                        }
                    }
                }
            }
        )
