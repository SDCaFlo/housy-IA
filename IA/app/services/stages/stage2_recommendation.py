def build_recommendation_response(resultados):
    if resultados:
        ids = [r["id"] for r in resultados]
        msg = "Estas propiedades podrían interesarte:\n\n"
        for i, r in enumerate(resultados, 1):
            msg += f"🏠 Propiedad #{i} (ID: {r['id']}): {r['text']}\n\n"
    else:
        ids = []
        msg = "No encontramos propiedades que coincidan."

    return msg, ids
