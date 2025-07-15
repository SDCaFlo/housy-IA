# IA/test_list_cities.py

from app.services.embeddings.opensearch_service import client as opensearch_client
import os

INDEX = os.getenv("OPENSEARCH_INDEX", "properties")

def list_indexed_cities():
    """
    Realiza una agregación de términos para listar todas las ciudades indexadas.
    """
    body = {
        "size": 0,
        "aggs": {
            "distinct_cities": {
                "terms": {
                    "field": "city.keyword",
                    "size": 100   # ajusta si esperas más de 100 ciudades
                }
            }
        }
    }
    resp = opensearch_client.search(index=INDEX, body=body)
    buckets = resp["aggregations"]["distinct_cities"]["buckets"]
    return [b["key"] for b in buckets]

if __name__ == "__main__":
    cities = list_indexed_cities()
    print("Ciudades indexadas en OpenSearch:")
    for c in cities:
        print("-", c)
