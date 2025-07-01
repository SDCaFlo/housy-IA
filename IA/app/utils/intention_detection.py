# app/utils/intention_detection.py

def tiene_intencion_busqueda(texto: str) -> bool:
    texto = texto.lower()
    claves = ["alquilar", "comprar", "buscar casa", "buscar departamento", "renta", "inmueble", "vivienda"]
    return any(palabra in texto for palabra in claves)
