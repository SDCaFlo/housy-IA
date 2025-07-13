# IA/app/utils/reverse_geocode.py

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import logging

# Creamos el geolocalizador
geolocator = Nominatim(user_agent="housy-ia")
# Para no exceder límites, pon un pequeño delay
reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)

def get_city_from_geo(lat: float, lon: float) -> str:
    """
    Dada lat/lon, devuelve el nombre de la ciudad o 'desconocida'.
    """
    try:
        location = reverse((lat, lon), language="es")
        if not location or "address" not in location.raw:
            return "desconocida"
        addr = location.raw["address"]
        # Busca claves comunes: city, town, village, municipality
        for key in ("city", "town", "village", "municipality", "county"):
            if key in addr:
                return addr[key].lower()
    except Exception as e:
        logging.warning(f"reverse_geocode falló: {e}")
    return "desconocida"
