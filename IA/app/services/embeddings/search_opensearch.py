# IA/app/services/embeddings/search_opensearch.py
import os
import logging
from app.services.embeddings.opensearch_service import client as opensearch_client
from app.services.embeddings.bedrock_service import embed_text
from botocore.exceptions import BotoCoreError, ClientError

INDEX = os.getenv("OPENSEARCH_INDEX", "properties")

def search_similar_properties(query: str, ciudad: str, k: int = 3) -> list[dict]:
    """
    Busca propiedades similares usando embeddings, filtradas por ciudad.
    """
    emb = embed_text(query)
    if not emb:
        logging.warning("Embedding vacío, retornando lista vacía")
        return []

    body = {
        "size": k,
        "query": {
            "bool": {
                "filter": {"term": {"city.keyword": ciudad.lower()}},
                "knn": {"embedding": {"vector": emb, "k": k}}
            }
        }
    }

    try:
        resp = opensearch_client.search(index=INDEX, body=body)
        hits = resp.get("hits", {}).get("hits", [])
        return [
            {"id": h["_id"],
             "text": h["_source"].get("text", ""),
             "score": h["_score"]}
            for h in hits
        ]
    except Exception as e:
        logging.error(f"Error en OpenSearch search: {e}")
        return []

def hay_propiedades_en_ciudad(ciudad: str) -> bool:
    """
    Verifica si hay al menos 1 propiedad en la ciudad.
    """
    body = {"size": 1, "query": {"term": {"city.keyword": ciudad.lower()}}}
    try:
        resp = opensearch_client.search(index=INDEX, body=body)
        return bool(resp.get("hits", {}).get("hits"))
    except Exception as e:
        logging.error(f"Error en OpenSearch hay_propiedades: {e}")
        return False
