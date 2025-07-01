import os
import hashlib
import psycopg2
from dotenv import load_dotenv
from app.services.embeddings.opensearch_service import client
from app.services.embeddings.bedrock_service import embed_text

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

def create_index_if_not_exists():
    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(
            index=INDEX_NAME,
            body={
                "settings": {
                    "index": {
                        "knn": True
                    }
                },
                "mappings": {
                    "properties": {
                        "text": {"type": "text"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": 1536
                        }
                    }
                }
            }
        )
        print(f"✅ Índice '{INDEX_NAME}' creado en OpenSearch")
    else:
        print(f"✅ Índice '{INDEX_NAME}' ya existe en OpenSearch")

# Crear índice si no existe
create_index_if_not_exists()

# Extraer propiedades desde PostgreSQL
cursor.execute("""
    SELECT title, description, property_type, address, operation_type
    FROM properties
""")
rows = cursor.fetchall()

indexados = 0

for row in rows:
    title, description, ptype, address, op = row
    text = f"{title} - {description} - {ptype} - {address} - {op}"

    # Crear ID único con hash para evitar duplicados
    unique_string = f"{title}-{address}"
    doc_id = hashlib.md5(unique_string.encode()).hexdigest()

    # Verificar si ya existe en OpenSearch
    if client.exists(index=INDEX_NAME, id=doc_id):
        continue  # Saltar si ya está

    embedding = embed_text(text)

    doc = {
        "text": text,
        "embedding": embedding
    }

    client.index(index=INDEX_NAME, id=doc_id, body=doc)
    indexados += 1

print(f"✅ Se indexaron {indexados} nuevas propiedades en OpenSearch")

cursor.close()
conn.close()
