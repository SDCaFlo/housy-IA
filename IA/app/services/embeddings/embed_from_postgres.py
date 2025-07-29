import os
import psycopg2
import logging
from dotenv import load_dotenv
from opensearchpy import OpenSearch, helpers
from app.services.embeddings.bedrock_service import embed_text

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Conexión a PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    database=os.getenv("POSTGRES_DB")
)
cursor = conn.cursor()

# Cliente de OpenSearch
client = OpenSearch(
    hosts=[{"host": os.getenv("OPENSEARCH_HOST"), "port": 443}],
    http_auth=(os.getenv("OPENSEARCH_USERNAME"), os.getenv("OPENSEARCH_PASSWORD")),
    use_ssl=True,
    verify_certs=True,
    timeout=60,
)

INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "properties")

def create_index_if_not_exists():
    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(
            index=INDEX_NAME,
            body={
                "settings": {"index": {"knn": True}},
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "title": {"type": "text"},
                        "description": {"type": "text"},
                        "property_type": {"type": "keyword"},
                        "operation_type": {"type": "keyword"},
                        "location": {"type": "keyword"},
                        "address": {"type": "text"},
                        "status": {"type": "keyword"},
                        "text": {"type": "text"},
                        "embedding": {"type": "knn_vector", "dimension": 1536}
                    }
                }
            }
        )
        logging.info(f"✅ Índice '{INDEX_NAME}' creado en OpenSearch")
    else:
        logging.info(f"ℹ️ Índice '{INDEX_NAME}' ya existe")

# Crear índice si no existe
create_index_if_not_exists()

# Consultar propiedades
cursor.execute("""
    SELECT id, title, description, property_type, operation_type, location, address, status
    FROM properties
""")
rows = cursor.fetchall()

def generate_actions(rows):
    for pid, title, desc, ptype, op_type, location, address, status in rows:
        text = f"{title} – {desc} – {ptype} – {op_type} – {address} – {status}"
        yield {
            "_op_type": "index",
            "_index": INDEX_NAME,
            "_id": str(pid),
            "_source": {
                "id": str(pid),
                "title": title,
                "description": desc,
                "property_type": ptype,
                "operation_type": op_type,
                "location": location,
                "address": address,
                "status": status,
                "text": text,
                "embedding": embed_text(text),
            }
        }

# Indexar en OpenSearch
logging.info(f"🔄 Indexando {len(rows)} propiedades en lotes de 20...")

success, _ = helpers.bulk(client, generate_actions(rows), chunk_size=20)

logging.info(f"✅ Se indexaron {success} documentos correctamente.")

cursor.close()
conn.close()
