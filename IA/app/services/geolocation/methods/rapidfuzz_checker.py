from rapidfuzz import process,fuzz

location_catalog = location_catalog = {
 'ancon': {'lat': -11.7750, 'lon':-77.1750},
 'ate': {'lat': -12.0561, 'lon': -76.9346},
 'barranco': {'lat': -12.147, 'lon': -77.0219},
 'breña': {'lat': -12.0562, 'lon': -77.0465},
 'carabayllo': {'lat': -11.8902, 'lon': -77.0415},
 'chaclacayo': {'lat': -11.9811, 'lon': -76.7703},
 'chorrillos': {'lat': -12.1856, 'lon': -77.0127},
 'cieneguilla': {'lat': -12.0664, 'lon': -76.755},
 'comas': {'lat': -11.9395, 'lon': -77.0465},
 'el agustino': {'lat': -12.0484, 'lon': -77.0028},
 'independencia': {'lat': -11.9911, 'lon': -77.0611},
 'jesús maría': {'lat': -12.0761, 'lon': -77.0434},
 'la molina': {'lat': -12.0895, 'lon': -76.9397},
 'la victoria': {'lat': -12.0741, 'lon': -77.0122},
 'lima': {'lat': -12.0464, 'lon': -77.0428},
 'lince': {'lat': -12.0861, 'lon': -77.0345},
 'los olivos': {'lat': -11.9621, 'lon': -77.0587},
 'lurigancho': {'lat': -11.9875, 'lon': -76.8322},
 'lurín': {'lat': -12.2794, 'lon': -76.871},
 'magdalena del mar': {'lat': -12.0905, 'lon': -77.0707},
 'miraflores': {'lat': -12.12, 'lon': -77.03},
 'pachacámac': {'lat': -12.1966, 'lon': -76.8447},
 'pucusana': {'lat': -12.4827, 'lon': -76.7964},
 'pueblo libre': {'lat': -12.077, 'lon': -77.0704},
 'puente piedra': {'lat': -11.8667, 'lon': -77.0744},
 'punta hermosa': {'lat': -12.319, 'lon': -76.8333},
 'punta negra': {'lat': -12.3725, 'lon': -76.7947},
 'rímac': {'lat': -12.0333, 'lon': -77.0167},
 'san bartolo': {'lat': -12.3833, 'lon': -76.7833},
 'san borja': {'lat': -12.1047, 'lon': -77.0103},
 'san isidro': {'lat': -12.1, 'lon': -77.0333},
 'san juan de lurigancho': {'lat': -12.0111, 'lon': -76.9994},
 'san juan de miraflores': {'lat': -12.1667, 'lon': -76.9667},
 'san luis': {'lat': -12.0689, 'lon': -77.0058},
 'san martín de porres': {'lat': -11.9833, 'lon': -77.0667},
 'san miguel': {'lat': -12.0786, 'lon': -77.0889},
 'santa anita': {'lat': -12.05, 'lon': -76.9667},
 'santa maría del mar': {'lat': -12.3936, 'lon': -76.7772},
 'santa rosa': {'lat': -11.8167, 'lon': -77.1667},
 'santiago de surco': {'lat': -12.1333, 'lon': -77.0},
 'surquillo': {'lat': -12.1167, 'lon': -77.0167},
 'villa el salvador': {'lat': -12.2167, 'lon': -76.9333},
 'villa maría del triunfo': {'lat': -12.1667, 'lon': -76.9333}
}

#lista de distritos
distritos = [key for key in location_catalog.keys()]

def check_fuzz(input:str)-> tuple[str, float, dict]:
    """uses fuzzy checker for words
    example result:
    ('ancon', 80.0, {'lat': -11.775, 'lon': -77.175})
    """
    best_match = process.extractOne(
    input,
    distritos,
    scorer=fuzz.WRatio
    )

    location = best_match[0]
    confidence = best_match[1]
    coordinates = location_catalog.get(location)
    
    return location, confidence, coordinates


