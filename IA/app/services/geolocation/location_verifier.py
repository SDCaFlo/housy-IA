from app.services.geolocation.methods.opencage_service import forward_search
from app.services.geolocation.methods.rapidfuzz_checker import check_fuzz

def verify_location(input_location: str)->tuple[str, dict]:
    """Realiza chequeo secuencial de direcciones
    formato: 
    ('los olivos', {'lat': -12.389822, 'lng': -76.7805897})"""
    #1. Chequeo fuzzy
    location, score, coordinates = check_fuzz(input_location)
    if score >= 80:
        print('resultado obtenido con fuzzy')
        return location, coordinates
    #2. Fallback Chequeo opencage
    else:
        print('resultado obtenido con opencage')
        return forward_search(input_location)
        
    
