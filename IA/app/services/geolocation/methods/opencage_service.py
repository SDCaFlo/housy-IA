from app.core.config import OPENCAGE_API_KEY
from opencage.geocoder import OpenCageGeocode

api_key = OPENCAGE_API_KEY
geocoder = OpenCageGeocode(api_key)


class LocationError(Exception):
    pass


def forward_search(
    search_location: str,
    area: str = "Lima Metropolitana",
    countrycode: str = "PE",
    proximity: dict = {"lat": -12.0464, "lon": -77.0428},
) -> tuple[str, dict]:
    """Uses forward search to convert text to coordinates"""
    # Formatting input data
    full_search_location = f"{area}, {search_location}"
    proximity_lat = str(proximity.get("lat", "-12.0464"))
    proximity_lng = str(proximity.get("lon", "-77.0428"))
    proximity_search = f"{proximity_lat},{proximity_lng}"

    # Searching for results
    results = geocoder.geocode(
        full_search_location,
        countrycode=countrycode,
        proximity=proximity_search,
        language="es",
    )
    try:
        best_result = results[0]
    except Exception:
        raise LocationError(f"Se introdujo una dirección inválida: {search_location}")

    formatted_name = best_result.get(
        "formatted"
    )  # .i.e.: 'San Bartolo, Lima Metropolitana, Perú'
    coordinates = best_result.get(
        "geometry"
    )  # result format:{'lat': -12.389822, 'lng': -76.7805897}

    coordinates["lon"] = coordinates[
        "lng"
    ]  # aqui agregamos LON para hacer match con nuestro formato
    coordinates.pop("lng")

    return formatted_name, coordinates
