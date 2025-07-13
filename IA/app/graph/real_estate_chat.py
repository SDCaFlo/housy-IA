# IA/app/graph/real_estate_chat.py
from app.services.embeddings.extract_city_opensearch import extract_city_opensearch
from app.services.embeddings.search_opensearch import hay_propiedades_en_ciudad, search_similar_properties

def run_chatbot_flow(user_message: str) -> dict:
    # 1) Extraer ciudad desde OpenSearch
    ciudad = extract_city_opensearch(user_message)

    # 2) Verificar si hay propiedades
    if ciudad == "desconocida" or not hay_propiedades_en_ciudad(ciudad):
        return {
            "stage": 1,
            "respuesta": f"No tenemos propiedades en '{ciudad.title()}'. Intenta con otra ciudad en Perú.",
            "resultados": [],
            "ids": []
        }

    # 3) Si hay, buscar recomendaciones
    resultados = search_similar_properties(user_message, ciudad=ciudad, k=3)
    texto = "🏡 Estas propiedades podrían interesarte:\n\n"
    ids = []
    for i, r in enumerate(resultados, 1):
        texto += f"🏠 Propiedad #{i} (ID: {r['id']}): {r['text']}\n\n"
        ids.append(r["id"])

    return {
        "stage": 2,
        "respuesta": texto,
        "resultados": resultados,
        "ids": ids
    }
