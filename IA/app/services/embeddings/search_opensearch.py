from app.core.aws_clients import get_opensearch_client
from app.services.embeddings.bedrock_service import embed_text
from app.core.config import OPENSEARCH_INDEX


def search_similar_properties(query_text, k=5):
    query_vector = embed_text(query_text)

    client = get_opensearch_client()
    
    response = client.search(
        index=OPENSEARCH_INDEX,
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
