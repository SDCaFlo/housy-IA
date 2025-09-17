import os
import sys
import time

project_root = os.path.abspath(os.path.join(os.getcwd(), "."))
print(f"project root: {project_root}")
sys.path.append(project_root)
import psycopg2
from dotenv import load_dotenv
from opensearchpy.helpers import bulk
from app.services.embeddings.bedrock_service import embed_text
from app.core.aws_clients import get_opensearch_client

# Cargar variables de entorno
load_dotenv()

# Conexión a PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("POSTGRESQL_DEV_URL"),
    port=os.getenv("POSTGRESQL_PORT"),
    user=os.getenv("POSTGRESQL_DEV_USER"),
    password=os.getenv("POSTGRESQL_DEV_PASSWORD"),
    database=os.getenv("POSTGRESQL_DEV_DB"),
)
cursor = conn.cursor()

# Cliente de OpenSearch
client = get_opensearch_client()

INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "properties")


def create_index_if_not_exists():
    if client.indices.exists(index=INDEX_NAME):
        print(f"Eliminando índice existente: {INDEX_NAME}")
        client.indices.delete(index=INDEX_NAME)

    if not client.indices.exists(index=INDEX_NAME):
        print("Creando indice nuevamente")
        client.indices.create(
            index=INDEX_NAME,
            body={
                "settings": {"index": {"knn": True}},
                "mappings": {
                    "properties": {
                        "property_id": {"type": "keyword"},
                        "title": {"type": "text"},
                        "unified_description": {"type": "text"},
                        "description_embedding": {
                            "type": "knn_vector",
                            "dimension": 1536,
                        },
                        "price": {"type": "double"},
                        "geolocation": {"type": "geo_point"},
                        "address": {"type": "text"},
                        "property_type": {"type": "keyword"},
                        "operation_type": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "location": {"type": "keyword"},
                        "space_count_by_type": {"type": "object", "dynamic": True},
                        "_audit_date": {"type": "date"},
                        "_indexed_at": {"type": "date"},
                        "_operation": {"type": "text"},
                    }
                },
            },
        )


def index_properties_from_view(batch_size=50):
    # Extraer propiedades desde PostgreSQL
    cursor.execute("""
    SELECT * FROM properties_index_base
    ORDER BY property_id ASC
    """)

    batch = []
    processed = 0

    print("Iniciando indexacion")

    while True:
        rows = cursor.fetchmany(batch_size)
        column_names = [desc[0] for desc in cursor.description]
        if not rows:
            break

        for index, row in enumerate(rows):
            print(f"procesando fila {index}")
            doc = dict(zip(column_names, row))

            # Asegurarse que title y description existan
            title = doc.get("title") or ""
            desc = doc.get("unified_description") or ""
            address = doc.get("address") or ""
            location = doc.get("location") or ""

            # Generar vectores
            description_embedding = embed_text(
                title + " " + desc + " " + location + " " + address
            )

            # Documento para OpenSearch
            os_doc = {
                "property_id": str(doc.get("property_id")),
                "title": title,
                "unified_description": desc,
                "description_embedding": description_embedding,
                "price": float(doc.get("price") or 0),
                # geolocalizacion
                "geolocation": {
                    "lat": float(doc.get("latitude") or 0),
                    "lon": float(doc.get("longitude") or 0),
                },
                "address": address,
                "property_type": doc.get("property_type"),
                "operation_type": doc.get("operation_type"),
                "status": doc.get("status"),
                "location": location,
                "space_count_by_type": doc.get("space_count_by_type"),
                "_operation": "new",
                "_indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

            batch.append(
                {
                    "_index": INDEX_NAME,
                    "_id": str(doc.get("property_id")),
                    "_source": os_doc,
                }
            )

        if batch:
            success, _ = bulk(client, batch)
            processed += success
            print(f"Indexados: {processed} documentos")
            batch.clear()


# Crear índice si no existe
create_index_if_not_exists()
index_properties_from_view()
