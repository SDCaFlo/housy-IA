from app.services.llm_contact import call_model

def handle(conversation):
    prompt = (
        "Simula ser un asesor inmobiliario que guía al usuario con preguntas "
        "para entender qué tipo de propiedad desea (ubicación, tipo, características). "
        "No respondas con recomendaciones aún. Sé breve (máx 50 palabras)."
    )
    return call_model(conversation, prompt)
