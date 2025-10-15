from langchain_core.tools import tool
from typing import Tuple
import requests


# Creamos una tool con el tool decorator
@tool
def geocode_address(address: str) -> Tuple[float, float, str]:
    """Convierte una posible locación en dirección normalizada.

    Esta herramienta es útil para:
    - Confirmar una localización brindada por cliente, si esta no es completamente clara.
    - Normalizar y completar direcciones parciales o informales
    - Verificar la existencia y precisión de ubicaciones

    Args:
    address (str): Dirección o ubicación en texto libre. Puede incluir:
        - Nombres de barrios/distritos (ej: "Miraflores", "San Isidro")
        - Direcciones completas (ej: "Av. Larco 345, Miraflores")
        - Nombres de lugares conocidos (ej: "Parque Kennedy")

    Returns:
    Tuple[float, float, str]: Una tupla con:
        - latitud (float): Coordenada de latitud
        - longitud (float): Coordenada de longitud
        - display_name (str): Dirección completa y normalizada

    Ejemplo de uso:
        Para "Miraflores" devuelve: (-12.1204, -77.0282, "Miraflores, Lima Metropolitana, Lima, Perú")
    """

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {
        "User-Agent": "my-chatbot-app/1.0 (housycorp@gmail.com)"  # posible cambiar.
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Error en la solicitud: {response.status_code}")

    data = response.json()

    if not data:
        return None  # No se encontró dirección

    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])
    display_name = str(data[0]["display_name"])
    return lat, lon, display_name
