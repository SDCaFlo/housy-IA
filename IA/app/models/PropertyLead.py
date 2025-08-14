from pydantic import BaseModel, Field
from typing import Optional,  List, Generic, TypeVar
from enum import Enum

class SlotState(str, Enum):
    """Estado del slot.
    - missing: valor faltante
    - pending_validation: pendiente de validación
    - validated: campo validado"""
    MISSING = 'missing'
    PENDING_VALIDATION = 'pending_validation'
    VALIDATED = 'validated'

class PropertyType(str, Enum):
    """Tipo de propiedad que se busca:
    - departamento
    - mini-departamento
    - casa
    - oficina
    - local"""
    DEPARTAMENTO = "departamento"
    MINI_DEPARTAMENTO = "mini-departamento"
    CASA = "casa"
    OFICINA = "oficina"
    LOCAL = "local"

class OperationType(str, Enum):
    """Tipo de operación de bien raíz: alquiler o venta"""
    ALQUILER = "alquiler"
    VENTA = "venta"

T = TypeVar("T") # Slot Genérico

class Slot(BaseModel, Generic[T]):
    """Clase genérica para SLOT. Permite tipado flexible."""
    value: Optional[T] = None
    state: SlotState= SlotState.MISSING
    required: bool = False

class Range(BaseModel, Generic[T]):
    """Rango numérico con mínimo y máximo"""
    min: Optional[T] = None
    max: Optional[T] = None

class PropertySearchParams(BaseModel):
    """Esquema para extracción NER"""

    ## Valores requeridos
    property_types: Optional[Slot[List[PropertyType]]] = Field(
        default_factory= lambda: Slot[List[PropertyType]](value=None, state='missing', required=True),
        description=
        'Objeto Slot que contiene: '
        'value: lista de tipos de propiedades (Ejemplo: ["departamento", "casa"]), '
        'state: "missing"'
        'required: True'
    )
    
    operation_types: Optional[Slot[OperationType]] = Field(
        default_factory= lambda: Slot[OperationType](value=None, state='missing', required=True),
        description=
        'Objeto Slot que contiene: '
        'value: Tipo de operación a realizar con la propiedad: Ejemplo: "alquiler"'
        'state: "missing"'
        'required: True'
    )

    location: Optional[Slot[str]] = Field(
        default_factory= lambda: Slot[str](value=None, state='missing', required=True)
        ,description=
        'Objeto Slot que contiene: '
        'value: Dirección de la propiedad (País, Ciudad, Distrito, Zona). Ejemplo: "Lima, Miraflores"'
        'state: "missing"'
        'required: True'
    )
    
    price_range: Optional[Slot[Range[float]]] = Field(
        default_factory= lambda: Slot[Range[float]](value=None, state='missing', required=True),
        description=
        'Objeto Slot que contiene: '
        'value: Rango de precios de la propiedad en dólares. Ejemplo: {"min": 1000.0, "max": 2000.0}'
        'state: "missing"'
        'required: True'
    )
    
    area_range: Optional[Slot[Range[float]]] = Field(
        default_factory= lambda: Slot[Range[float]](value=None, state='missing', required=True),
        description=
        'Objeto Slot que contiene: '
        'value: Rango de área de la propiedad en metros cuadrados (m2), Ejemplo: {"min":60.0, "max": 100.0}'
        'state: "missing"'
        'required: True'
    )

    bedroom_quantity_range: Optional[Slot[Range[int]]] = Field(
        default_factory= lambda: Slot[Range[int]](value=None, state='missing', required=True),
        description=
        'Objeto Slot que contiene: '
        'value: Rango de cantidad mínima y máxima de habitaciones deseadas, Ejemplo: {"min": 1, "max": 3}'
        'state: "missing"'
        'required: True'
    )

    bathroom_quantity_range: Optional[Slot[Range[int]]] = Field(
        default_factory= lambda: Slot[Range[int]](value=None, state='missing', required=False),
        description=
        'Objeto Slot que contiene: '
        'Rango de cantidad mínima y máxima de baños deseadas, Ejemplo: {"min": 1, "max": 2}'
        'state: "missing"'
        'required: False'
    )

# from pydantic import BaseModel, Field, field_validator
# from typing import Optional,  List, Union
# from enum import Enum

# class PropertyLead(BaseModel):
#     # clase básica para el input de mensaje
#     # Obligatorias 
#     ubicacion: Union[str, None] = Field(default=None, description='ciudad, distrito, barrio, etc')
#     tipo_propiedad: Optional[List[str]] = Field(default=None, description='casa, departamento, cuarto, oficina, terreno, etc')
#     transaccion: Union[str, None] = Field(default=None, description='compra o alquiler')
#     # Opcionales
#     presupuesto: Optional[int] = Field(default=None, description='Presupuesto aproximado en dolares o soles')
#     numero_dormitorios: Optional[int] = Field(default=None, description='Cantidad mínima de dormitorios')
#     numero_banos: Optional[int] = Field(default=None, description="Número mínimo de baños.")
#     metraje_minimo: Optional[int] = Field(default=None, description='Área mínima en metros cuadrados')
#     amenidades: Optional[List[str]] = Field(default=None, description="Lista de amenidades deseadas: gimnasio, piscina, etc")
#     cercania: Optional[List[str]] = Field(default=None, description="Lista de cercanías: cerca a la playa, plaza, centro comercial, etc")
#     pet_friendly: Optional[bool] = Field(default=None, description="Si busca llevar una mascota.")


# class PropertyType(str, Enum):
#     DEPARTAMENTO = "departamento"
#     MINI_DEPARTAMENTO = "mini-departamento"
#     CASA = "casa"
#     OFICINA = "oficina"
#     LOCAL = "local"

# class OperationType(str, Enum):
#     ALQUILER = "alquiler"
#     VENTA = "venta"

# class PropertySearchParams(BaseModel):
#     """Esquema para parámetros extraídos de la conversación"""

#     # Criterios básicos
#     property_types: Optional[List[PropertyType]] = Field(
#         default=[], 
#         description='Lista de tipos de propiedades deseados (ej: ["departamento", "casa", "mini-departamento", "local", "oficina"])'
#     )
#     operation_type: Optional[OperationType] = Field(None, description='Tipo de operación: Opciones: "alquiler" o "venta"')

#     # Rango de precios
#     min_price: Optional[float] = Field(None, description='Precio mínimo expresado en moneda local')
#     max_price: Optional[float] = Field(None, description='Precio máximo expresado en moneda local')

#     # Ubicación
#     location: Optional[List[str]] = Field(None, description='Lista ubicaciones deseadas en cualquier nivel: (Ej.: ciudad, distrito, zona)')

#     # Características físicas
#     min_bedrooms: Optional[int] = Field(None, description='Cantidad mínima de dormitorios requeridos')
#     max_bedrooms: Optional[int] = Field(None, description='Cantidad máxima de dormitorios aceptables')
#     min_bathrooms: Optional[int] = Field(None, description='Cantidad mínima de baños requeridos')
#     min_area: Optional[float] = Field(None, description='Área mínima de la propiedad en m2 (metros cuadrados)')
#     max_area: Optional[float] = Field(None, description='Área máxima de la propiedad en m2 (metros cuadrados)')
#     min_floor: Optional[int] = Field(None, description='Piso mínimo (ej: 2, excluye el primer piso)')
#     max_floor: Optional[int] = Field(None, description='Piso máximo deseado')

#     # Areas de la casa
#     house_spaces: Optional[List[str]] = Field(
#         default=[],
#         description = 'Lista de ambientes del hogar deseados (ej: ["comedor", "sala", "patio", "cocina", etc...])'
#     )

#     # Amenidades
#     amenities_wanted: Optional[List[str]] = Field(
#         default=[],
#         description='Lista de equipamientos o servicios internos deseados (ej: ["piscina","gym","parking", etc...])'
#     )

#     # Cercanías
#     nearby_places: Optional[List[str]] = Field(
#         default=[],
#         description='Lugares o servicios externos cercanos deseados (ej: ["gym", "colegio", "parque", "centro comercial", "hospital", etc...])'
#     )

#     #Exclusiones
#     amenities_exclude: Optional[List[str]] = Field(
#         default=[],
#         description='Lista de amenidades internas que el cliente desea evitar'
#     )
#     nearby_places_exclude: Optional[List[str]] = Field(
#         default=[],
#         description='Lugares o servicios cercanos que el cliente quiere evitar'
#     )
#     house_spaces_exclude: Optional[List[str]] = Field(
#         default=[],
#         description = 'Ambientes internos no deseados'
#     )

#     #Validators
#     @field_validator('max_price')
#     @classmethod
#     def validate_price_range(cls, v, values):
#         """Valida que los rangos sean válidos"""
#         min_price = values.data.get('min_price')
#         if min_price and v is not None and v < min_price:
#             raise ValueError('max_price debe ser mayor que min_price')
#         return v

#     @classmethod
#     def describe_class(cls) -> str:
#         """Describe los parámetros de la clase"""
#         data_context = ""
#         for key,value in dict(cls.model_fields.items()).items():
#             data_info = key +  ": " + value.description
#             data_context += data_info + "\n"
#         return data_context.strip("\n")
    
#     @classmethod    
#     def get_sample_element(cls):
#         """Retorna un ejemplo de la clase"""
#         data_dict = {
#             'property_types': ['departamento', 'casa'],
#             'operation_type': 'alquiler',
#             'min_price': 2000.0,
#             'max_price': 3000.0,
#             'location': ['Miraflores, Lima, Perú', 'Buenos Aires, Capital Federal, Argentina'],
#             'min_bedrooms': 2,
#             'max_bedrooms': None,
#             'min_area': 70,
#             'max_area': 100,
#             'min_floor': None,
#             'max_floor': None,
#             'house_spaces': ['comedor', 'sala'],
#             'amenities_wanted': ['coworking', 'gimnasio'],
#             'nearby_places': ['hospital', 'supermercado'],
#             'amenities_exclude': [],
#             'nearby_places_exclude': [],
#             'house_spaces_exclude': []
#         }

#         return dict(cls(**data_dict))
        
