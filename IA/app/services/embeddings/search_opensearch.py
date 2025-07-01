from app.services.embeddings.opensearch_service import client
from app.services.embeddings.bedrock_service import embed_text
import os

INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "properties")

def search_similar_properties(query_text, k=5):
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
            "text": hit["_source"]["text"],
            "score": hit["_score"]
        }
        for hit in response["hits"]["hits"]
    ]

    print("DEBUG: Resultados de búsqueda crudos:", results)  # <-- aquí

    return results
