# IA/app/utils/intention_detection.py

def tiene_intencion_busqueda(texto: str) -> bool:
    """Detecta si el texto del usuario tiene intención de búsqueda de propiedades"""
    palabras_clave = [
        "busco", "necesito", "quiero", "buscar", 
        "propiedad", "departamento", "casa", "alquilar", "comprar", 
        "en venta", "con jardín", "con piscina", "barato", "amplio", "zona"
    ]
    texto = texto.lower()
    return any(palabra in texto for palabra in palabras_clave)
