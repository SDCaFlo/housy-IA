import os
import logging
from app.services.embeddings.bedrock_service import embed_text
from app.core.aws_clients import get_opensearch_client

INDEX = os.getenv("OPENSEARCH_INDEX", "properties")

def search_similar_properties(query: str) -> list:
    """
    Busca propiedades similares usando embeddings, filtradas por ciudad.
    """   

    try:
        client = get_opensearch_client()
        resp = client.search(index=INDEX, body=query)
        hits = resp.get("hits", {}).get("hits", [])
        return [
            {"id": h["_id"],
             "description": h["_source"].get("unified_description", ""),
             "property_type": h["_source"].get("property_type", ""),
             "operation_type": h["_source"].get("operation_type", ""),
             "address": h["_source"].get("address", ""),
             "price": h["_source"].get("price", ""),
             "score": h["_score"]}
            for h in hits
        ]
    except Exception as e:
        logging.error(f"Error en OpenSearch search: {e}")
        return []