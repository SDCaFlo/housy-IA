import os
import json
import boto3
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

    try:
        # 🔍 Cliente RDS Data API (SIN psycopg2)
        rds_client = boto3.client('rds-data')
        
        # 🔍 Cliente OpenSearch
        opensearch = OpenSearch(
            hosts=[{'host': os.environ['OPENSEARCH_HOST'], 'port': 443}],
            http_auth=(os.environ['OPENSEARCH_USER'], os.environ['OPENSEARCH_PASS']),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

        # 🗂️ Buscar registros pendientes en auditoría
        response = rds_client.execute_statement(
            resourceArn=os.environ['RDS_CLUSTER_ARN'],
            secretArn=os.environ['RDS_SECRET_ARN'], 
            database=os.environ['DB_NAME'],
            sql="""
                SELECT id, property_id, accion 
                FROM auditoria_indexacion 
                WHERE procesado = false 
                ORDER BY fecha ASC 
                LIMIT 10
            """
        )
        
        cambios = response['records']
        if not cambios:
            return {"statusCode": 200, "message": "No hay cambios pendientes"}

        procesados = 0

        for record in cambios:
            try:
                cambio_id = record[0]['longValue']
                property_id = record[1]['longValue']  
                accion = record[2]['stringValue']

                if accion in ('INSERT', 'UPDATE'):
                    # Obtener datos de la propiedad
                    prop_response = rds_client.execute_statement(
                        resourceArn=os.environ['RDS_CLUSTER_ARN'],
                        secretArn=os.environ['RDS_SECRET_ARN'],
                        database=os.environ['DB_NAME'],
                        sql="""
                            SELECT id, title, description, property_type, 
                                   operation_type, location, address, status
                            FROM properties 
                            WHERE id = :property_id
                        """,
                        parameters=[
                            {'name': 'property_id', 'value': {'longValue': property_id}}
                        ]
                    )
                    
                    if not prop_response['records']:
                        raise ValueError(f"Propiedad {property_id} no encontrada")
                    
                    # Construir documento
                    prop_data = prop_response['records'][0]
                    prop_id = prop_data[0]['longValue']
                    title = prop_data[1]['stringValue']
                    desc = prop_data[2]['stringValue'] 
                    prop_type = prop_data[3]['stringValue']
                    op_type = prop_data[4]['stringValue']
                    location = prop_data[5]['stringValue']
                    address = prop_data[6]['stringValue']
                    status = prop_data[7]['stringValue']
                    
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
                rds_client.execute_statement(
                    resourceArn=os.environ['RDS_CLUSTER_ARN'],
                    secretArn=os.environ['RDS_SECRET_ARN'],
                    database=os.environ['DB_NAME'],
                    sql="""
                        UPDATE auditoria_indexacion 
                        SET procesado = true 
                        WHERE id = :cambio_id
                    """,
                    parameters=[
                        {'name': 'cambio_id', 'value': {'longValue': cambio_id}}
                    ]
                )

                procesados += 1

            except Exception as e:
                print(f"⚠️ Error procesando {property_id}: {str(e)}")
                continue

        return {
            "statusCode": 200,
            "message": f"✅ Procesados {procesados} de {len(cambios)} registros"
        }

    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        return {
            "statusCode": 500,
            "error": str(e)
        }