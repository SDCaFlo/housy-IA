import os
import logging
from app.core.aws_clients import get_opensearch_client
import time

INDEX = os.getenv("OPENSEARCH_INDEX", "properties")


def search_similar_properties(query: str, max_retries:int = 3, backoff: float = 0.5) -> list:
    """
    Busca propiedades similares usando embeddings, filtradas por ciudad.
    """
    for attempt in range(1, max_retries + 1):
        try:
            client = get_opensearch_client()
            resp = client.search(index=INDEX, body=query)
            hits = resp.get("hits", {}).get("hits", [])
            return [
                {
                    "id": h["_id"],
                    "description": h["_source"].get("unified_description", ""),
                    "property_type": h["_source"].get("property_type", ""),
                    "operation_type": h["_source"].get("operation_type", ""),
                    "address": h["_source"].get("address", ""),
                    "price": h["_source"].get("price", ""),
                    "score": h["_score"],
                }
                for h in hits
            ]
        except Exception as e:
            logging.warning(
                "OpenSearch search failed (attempt %s/%s): %s",
                attempt,
                max_retries,
                e,
            )
            if attempt < max_retries:
                time.sleep(backoff * attempt)

    logging.error("OpenSearch search failed after %s attempts.", max_retries)
    return []
