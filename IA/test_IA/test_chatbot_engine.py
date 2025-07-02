
from app.services.embeddings.search_opensearch import search_similar_properties

query = "deseo una casa de alquiler en lima cerca de un río con 3 cuartos"
resultados = search_similar_properties(query)

print("🔍 Resultados desde OpenSearch:")
for r in resultados:
    print(f"ID: {r['id']} - Score: {r['score']:.4f}")
    print(r['text'])
    print("-" * 50)

   