from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Union


class PropertyLead(BaseModel):
    # clase básica para el input de mensaje
    # Obligatorias 
    ubicacion: Union[str, None] = Field(default=None, description='REQUERIDO: Ubicación deseada como ciudad o distrito, etc')
    tipo_propiedad: Union[str, None]  = Field(default=None, description='REQUERIDO: casa, departamento, cuarto, oficina, terreno, etc')
    transaccion: Literal["compra", "alquiler", None] = Field(default=None, description='REQUERIDO: compra o alquiler')
    # Opcionales
    presupuesto: Optional[float] = Field(default=None, description='Presupuesto aproximado en dolares o soles')
    numero_dormitorios: Optional[int] = Field(default=None, description='Cantidad mínima de dormitorios')
    numero_banos: Optional[int] = Field(default=None, description="Número mínimo de baños.")
    metraje_minimo: Optional[float] = Field(default=None, description='Área mínima en metros cuadrados')
    zona_preferida: Optional[str] = Field(default=None, description='Alguna zona preferida de la ciudad')
    amenidades: Optional[List[str]] = Field(default=None, description="Lista de amenidades deseadas.")
    pet_friendly: Optional[bool] = Field(default=None, description="Si busca llevar una mascota.")
    
