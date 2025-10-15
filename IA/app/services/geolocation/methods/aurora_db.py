
import psycopg2
from app.core.config import AURORA_DB_URL, AURORA_DB_USER, AURORA_DB_PASSWORD

DB_CONFIG = {
    'host': AURORA_DB_URL,
    'port': 5432,
    'database': 'locations',
    'user': AURORA_DB_USER,
    'password': AURORA_DB_PASSWORD
}

def get_db_connection():
    """Crear conexión a PostgreSQL"""
    return psycopg2.connect(**DB_CONFIG)


def smart_search_location(search_input, country_code='PE', limit=10):
    """
    Búsqueda inteligente que maneja:
    - Typos (búsqueda fuzzy)
    - Búsquedas compuestas: "Lima, San Isidro" o "San Isidro, Lima"
    - Nombres parciales
    
    Args:
        search_input: String de búsqueda (puede ser compuesto)
        country_code: Código de país para filtrar (default: PE)
        limit: Número máximo de resultados
    
    Returns:
        Lista de tuplas (id, name, type, full_path, lat, lon, score)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Detectar si es búsqueda compuesta (contiene coma)
    if ',' in search_input:
        parts = [p.strip() for p in search_input.split(',')]
        
        # Búsqueda jerárquica: "distrito, ciudad"
        query = """
            WITH search_terms AS (
                SELECT 
                    unnest(%s::text[]) as term,
                    generate_series(1, %s) as term_order
            ),
            matched_locations AS (
                SELECT DISTINCT ON (l.id)
                    l.id,
                    l.name,
                    l.type,
                    l.path,
                    ST_Y(l.centroid) as latitude,
                    ST_X(l.centroid) as longitude,
                    ST_AsGeoJSON(l.geom) as geometry,
                    get_location_full_path(l.id) as full_path,
                    nlevel(l.path) as specificity,
                    -- Score compuesto
                    (
                        -- Similitud del nombre principal
                        similarity(l.name_norm, normalize_name(st.term)) * 50 +
                        -- Bonus si coincide exacto
                        CASE WHEN l.name_norm = normalize_name(st.term) THEN 30 ELSE 0 END +
                        -- Bonus por tipo
                        CASE l.type
                            WHEN 'district' THEN 20
                            WHEN 'city' THEN 15
                            WHEN 'neighborhood' THEN 10
                            ELSE 5
                        END +
                        -- Penalización por distancia en orden de búsqueda
                        (5 - st.term_order) * 5
                    ) as match_score,
                    st.term_order
                FROM locations l
                CROSS JOIN search_terms st
                LEFT JOIN location_names ln ON ln.location_id = l.id
                WHERE 
                    (l.name_norm %% normalize_name(st.term) OR ln.name_norm %% normalize_name(st.term))
                    AND l.country_code = %s
            ),
            hierarchical_matches AS (
                SELECT 
                    m1.id,
                    m1.name,
                    m1.type,
                    m1.full_path,
                    m1.latitude,
                    m1.longitude,
                    m1.geometry,
                    -- Score total: suma de scores + bonus si hay relación jerárquica
                    COALESCE(SUM(m2.match_score), 0) +
                    CASE 
                        WHEN COALESCE(BOOL_OR(m1.path <@ m2.path OR m2.path <@ m1.path), false) THEN 50 
                        ELSE 0 
                    END as total_score
                FROM matched_locations m1
                LEFT JOIN matched_locations m2 ON m1.term_order != m2.term_order
                GROUP BY m1.id, m1.name, m1.type, m1.full_path, m1.latitude, m1.longitude, m1.geometry, m1.path
            )
            SELECT 
                id, name, type, full_path, latitude, longitude, total_score
            FROM hierarchical_matches
            ORDER BY total_score DESC, name
            LIMIT %s;
        """
        
        cursor.execute(query, (parts, len(parts), country_code, limit))
        
    else:
        # Búsqueda simple con fuzzy matching
        query = """
            SELECT DISTINCT
                l.id,
                l.name,
                l.type,
                get_location_full_path(l.id) as full_path,
                ST_Y(l.centroid) as latitude,
                ST_X(l.centroid) as longitude,
                ST_AsGeoJSON(l.geom) as geometry,
                -- Score compuesto
                (
                    GREATEST(
                        similarity(l.name_norm, normalize_name(%s)) * 100,
                        COALESCE(MAX(similarity(ln.name_norm, normalize_name(%s))) * 100, 0)
                    ) +
                    CASE l.type
                        WHEN 'district' THEN 20
                        WHEN 'city' THEN 15
                        WHEN 'neighborhood' THEN 10
                        ELSE 5
                    END +
                    CASE WHEN l.name_norm = normalize_name(%s) THEN 30 ELSE 0 END
                ) as score
            FROM locations l
            LEFT JOIN location_names ln ON ln.location_id = l.id
            WHERE 
                (l.name_norm %% normalize_name(%s) OR ln.name_norm %% normalize_name(%s))
                AND l.country_code = %s
            GROUP BY l.id, l.name, l.type, l.centroid, l.geom
            ORDER BY score DESC, l.name
            LIMIT %s;
        """
        
        cursor.execute(query, (
            search_input, search_input, search_input,
            search_input, search_input, country_code, limit
        ))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return results