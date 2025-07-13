# IA/app/services/embeddings/extract_city_opensearch.py
from app.services.embeddings.opensearch_service import client as opensearch_client

INDEX = "properties"

def extract_city_opensearch(user_text: str) -> str:
    """
    Intenta extraer la ciudad de user_text buscando coincidencias en el campo city.keyword.
    Devuelve la ciudad en minúsculas, o 'desconocida' si no hay hits.
    """
    body = {
        "size": 1,
        "query": {
            "match": {
                "city.keyword": {
                    "query": user_text,
                    "fuzziness": "AUTO",
                    "operator": "and"
                }
            }
        }
    }
    resp = opensearch_client.search(index=INDEX, body=body)
    hits = resp.get("hits", {}).get("hits", [])
    if not hits:
        return "desconocida"
    city = hits[0]["_source"].get("city", "").lower()
    return city
