CREATE TABLE IF NOT EXISTS auditoria_indexacion (
    id SERIAL PRIMARY KEY,
    property_id UUID,
    accion TEXT,
    descripcion TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
