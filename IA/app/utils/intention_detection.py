# IA/app/utils/intention_detection.py
def tiene_intencion_busqueda(texto: str) -> bool:
    """Detecta si el texto del usuario tiene intención de búsqueda de propiedades"""
    palabras_clave = [
        "busco", "necesito", "quiero", "buscar", "me interesa", "quisiera",
        "propiedad", "departamento", "casa", "alquilar", "comprar", 
        "en venta", "en alquiler", "renta", "arriendo",
        "con jardín", "con piscina", "con balcón", "terraza", 
        "barato", "amplio", "acogedor", "moderno", "zona segura",
        "habitaciones", "cuartos", "baños", "dormitorios",
        "1 dormitorio", "2 dormitorios", "3 dormitorios", "4 dormitorios",
        "1 cuarto", "2 cuartos", "3 cuartos", "4 cuartos",
        "de lujo", "económico", "cerca de"
    ]
    texto = texto.lower()
    return any(palabra in texto for palabra in palabras_clave)

