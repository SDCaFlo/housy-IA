import os
import json
import psycopg2
from opensearchpy import OpenSearch, RequestsHttpConnection
from bedrock_service import embed_text

def lambda_handler(event, context):
    # ✅ Modo de test simple
    if event.get("test"):
        print("🧪 Lambda funcionando correctamente (modo test)")
        return {
            "statusCode": 200,
            "body": "Test exitoso"
        }

    conn = None
    cur = None

    try:
        # 🔐 Conexión a PostgreSQL
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            dbname=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD']
        )
        cur = conn.cursor()

        # 🔍 Cliente OpenSearch
        opensearch = OpenSearch(
            hosts=[{'host': os.environ['OPENSEARCH_HOST'], 'port': 443}],
            http_auth=(os.environ['OPENSEARCH_USER'], os.environ['OPENSEARCH_PASS']),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

        # 🗂️ Buscar registros pendientes en auditoría
        cur.execute("""
            SELECT id, property_id, accion 
            FROM auditoria_indexacion 
            WHERE procesado = false 
            ORDER BY fecha ASC 
            LIMIT 10
        """)
        cambios = cur.fetchall()

        if not cambios:
            return {"statusCode": 200, "message": "No hay cambios pendientes"}

        procesados = 0

        for cambio_id, property_id, accion in cambios:
            try:
                if accion in ('INSERT', 'UPDATE'):
                    # Obtener datos de la propiedad
                    cur.execute("""
                        SELECT id, title, description, property_type, 
                               operation_type, location, address, status
                        FROM properties 
                        WHERE id = %s
                    """, (property_id,))
                    
                    prop_data = cur.fetchone()
                    if not prop_data:
                        raise ValueError(f"Propiedad {property_id} no encontrada")
                    
                    # Construir documento
                    prop_id, title, desc, prop_type, op_type, location, address, status = prop_data
                    texto = f"{title} {desc} {prop_type} {op_type} {address} {status}"
                    embedding = embed_text(texto)

                    doc = {
                        "id": str(prop_id),
                        "title": title,
                        "description": desc,
                        "property_type": prop_type,
                        "operation_type": op_type,
                        "location": location,
                        "address": address,
                        "status": status,
                        "text": texto,
                        "embedding": embedding
                    }

                    # Indexar en OpenSearch
                    opensearch.index(
                        index=os.environ['OPENSEARCH_INDEX'],
                        id=str(prop_id),
                        body=doc
                    )

                elif accion == 'DELETE':
                    opensearch.delete(
                        index=os.environ['OPENSEARCH_INDEX'],
                        id=str(property_id),
                        ignore=[404]
                    )

                # Marcar como procesado
                cur.execute("""
                    UPDATE auditoria_indexacion 
                    SET procesado = true 
                    WHERE id = %s
                """, (cambio_id,))

                procesados += 1

            except Exception as e:
                print(f"⚠️ Error procesando {property_id}: {str(e)}")
                continue

        conn.commit()

        return {
            "statusCode": 200,
            "message": f"✅ Procesados {procesados} de {len(cambios)} registros"
        }

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error general: {str(e)}")
        return {
            "statusCode": 500,
            "error": str(e)
        }

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
