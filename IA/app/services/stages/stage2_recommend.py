from app.services.embeddings.search_opensearch import search_similar_properties
from app.models.PropertyLead import PropertyLead

def handler(lead: PropertyLead)->list:
    """Invoca la búsqueda en opensearch en base a la description del lead"""
    lead_description = create_lead_description(lead)
    properties = search_similar_properties(lead_description)
    return properties


def create_lead_description(lead: PropertyLead) -> str:
    """Creación de lead description con las palabras de un diccionario"""
    lead = dict(lead)
    lead_description_list = []
    for key, value in lead.items():
        if value != None: 
            item_description = f"{key}: {value}"
            lead_description_list.append(item_description)
    
    return ", ".join(lead_description_list)

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