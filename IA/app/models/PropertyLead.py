from pydantic import BaseModel, Field
from typing import Optional,  List, Union


class PropertyLead(BaseModel):
    # clase básica para el input de mensaje
    # Obligatorias 
    ubicacion: Union[str, None] = Field(default=None, description='ciudad, distrito, barrio, etc')
    tipo_propiedad: Optional[List[str]] = Field(default=None, description='casa, departamento, cuarto, oficina, terreno, etc')
    transaccion: Union[str, None] = Field(default=None, description='compra o alquiler')
    # Opcionales
    presupuesto: Optional[int] = Field(default=None, description='Presupuesto aproximado en dolares o soles')
    numero_dormitorios: Optional[int] = Field(default=None, description='Cantidad mínima de dormitorios')
    numero_banos: Optional[int] = Field(default=None, description="Número mínimo de baños.")
    metraje_minimo: Optional[int] = Field(default=None, description='Área mínima en metros cuadrados')
    amenidades: Optional[List[str]] = Field(default=None, description="Lista de amenidades deseadas: gimnasio, piscina, etc")
    cercania: Optional[List[str]] = Field(default=None, description="Lista de cercanías: cerca a la playa, plaza, centro comercial, etc")
    pet_friendly: Optional[bool] = Field(default=None, description="Si busca llevar una mascota.")
    
