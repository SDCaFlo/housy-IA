from app.services.embeddings.opensearch_service import client
from .bedrock_service import embed_text

import os

INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "properties")

def search_similar_properties(query_text, k=5):
    try:
        query_vector = embed_text(query_text)

        response = client.search(
            index=INDEX_NAME,
            body={
                "size": k,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_vector,
                            "k": k
                        }
                    }
                }
            }
        )

        results = [
            {
                "id": hit["_source"].get("id", hit["_id"]),
                "text": hit["_source"].get("text", ""),
                "score": hit["_score"]
            }
            for hit in response["hits"]["hits"]
        ]

        return results

    except Exception as e:
        print("Error en búsqueda OpenSearch:", e)
        return []
