from app.services.embeddings.search_opensearch import search_similar_properties

query = "quiero alquilar una casa con piscina y tres cuartos en Lima"
results = search_similar_properties(query)

print("🔍 Resultados de búsqueda:")
for r in results:
    print(f"→ Score: {r['score']:.4f} | Texto: {r['text'][:60]}...")
