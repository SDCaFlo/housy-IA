-- 1. Crear o reemplazar la función que maneja INSERT, UPDATE y DELETE
CREATE OR REPLACE FUNCTION registrar_auditoria()
RETURNS trigger AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    INSERT INTO auditoria_indexacion (property_id, accion, descripcion)
    VALUES (
      OLD.id,
      TG_OP,
      CONCAT('Propiedad ', OLD.id, ' fue ', TG_OP)
    );
    RETURN OLD;
  ELSE
    INSERT INTO auditoria_indexacion (property_id, accion, descripcion)
    VALUES (
      NEW.id,
      TG_OP,
      CONCAT('Propiedad ', NEW.id, ' fue ', TG_OP)
    );
    RETURN NEW;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- 2. Eliminar cualquier trigger anterior
DROP TRIGGER IF EXISTS trigger_property_change ON properties;

-- 3. Crear trigger para INSERT, UPDATE y DELETE
CREATE TRIGGER trigger_property_change
AFTER INSERT OR UPDATE OR DELETE ON properties
FOR EACH ROW
EXECUTE FUNCTION registrar_auditoria();
