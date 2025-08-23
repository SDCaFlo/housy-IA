from pydantic import BaseModel, Field, model_validator, ConfigDict, computed_field
from typing_extensions import Self
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
    required: bool = False

    def merge_with(self, other: 'Slot[T]') -> 'Slot[T]':
        if other is None:
            return self
        if hasattr(self.value,'merge_with') and hasattr(other.value, 'merge_with'):
            self.value.merge_with(other.value)
        else:
            self.value = other.value
        return self
    
    @computed_field  # se recalcula al acceder, sin mutaciones internas
    def state(self) -> SlotState:
        return SlotState.VALIDATED if self.value is not None else SlotState.MISSING

class LocationSlot(Slot):
    value: Optional[str] = None
    required: bool = True
    lon: Optional[float] = None
    lat: Optional[float] = None

    @computed_field  
    def state(self) -> SlotState:
        if self.lon is not None:
            return SlotState.VALIDATED
        elif self.value is not None:
            return SlotState.PENDING_VALIDATION
        else:
            return SlotState.MISSING

class Range(BaseModel, Generic[T]):
    """Rango numérico con mínimo y máximo"""
    model_config = ConfigDict(validate_assignment=True)
    
    min: Optional[T] = None
    max: Optional[T] = None

    def merge_with(self, other: 'Range[T]') -> 'Range[T]':
        if other is None:
            return
        if other.min not in [None]:
            self.min = other.min
        if other.max not in [None]:
            self.max = other.max

    @model_validator(mode='after')
    def check_valid_range(self)->Self:
        if self.min is not None and self.min < 0 :
            raise ValueError("model_validator: Negative value")
        if self.max is not None and self.max < 0 :
            raise ValueError("model_validator: Negative value")
        if self.max is not None and self.min is not None:
            if self.max < self.min:
                raise ValueError("mode_validator: Invalid range max<min")
             
        return self


class PropertySearchParams(BaseModel):    
    """Esquema para extracción NER"""

    ## Valores requeridos
    property_types: Optional[Slot[List[PropertyType]]] = Field(
        default_factory= lambda: Slot[List[PropertyType]](value=None, required=True),
        description=
        'Objeto Slot que contiene: '
        'value: lista de tipos de propiedades (Ejemplo: ["departamento", "casa"]), '
        'state: "missing"'
        'required: True'
    )
    
    operation_types: Optional[Slot[OperationType]] = Field(
        default_factory= lambda: Slot[OperationType](value=None, required=True),
        description=
        'Objeto Slot que contiene: '
        'value: Tipo de operación a realizar con la propiedad: Ejemplo: "alquiler"'
        'state: "missing"'
        'required: True'
    )

    location: Optional[LocationSlot] = Field(
        default_factory= lambda: LocationSlot(value=None, required=True)
        ,description=
        'Objeto Slot que contiene: '
        'value: Dirección de la propiedad (País, Ciudad, Distrito, Zona). Ejemplo: "Lima, Miraflores"'
        'state: "missing"'
        'required: True'
    )
    
    price_range: Optional[Slot[Range[float]]] = Field(
        default_factory= lambda: Slot[Range[float]](value=None, required=True),
        description=
        'Objeto Slot que contiene: '
        'value: Rango de precios de la propiedad en dólares. Ejemplo: {"min": 1000.0, "max": 2000.0}'
        'state: "missing"'
        'required: True'
    )
    
    area_range: Optional[Slot[Range[float]]] = Field(
        default_factory= lambda: Slot[Range[float]](value=None, required=True),
        description=
        'Objeto Slot que contiene: '
        'value: Rango de área de la propiedad en metros cuadrados (m2), Ejemplo: {"min":60.0, "max": 100.0}'
        'state: "missing"'
        'required: True'
    )

    bedroom_quantity_range: Optional[Slot[Range[int]]] = Field(
        default_factory= lambda: Slot[Range[int]](value=None, required=True),
        description=
        'Objeto Slot que contiene: '
        'value: Rango de cantidad mínima y máxima de habitaciones deseadas, Ejemplo: {"min": 1, "max": 3}'
        'state: "missing"'
        'required: True'
    )

    bathroom_quantity_range: Optional[Slot[Range[int]]] = Field(
        default_factory= lambda: Slot[Range[int]](value=None, required=False),
        description=
        'Objeto Slot que contiene: '
        'Rango de cantidad mínima y máxima de baños deseadas, Ejemplo: {"min": 1, "max": 2}'
        'state: "missing"'
        'required: False'
    )

    def merge_with(self, other: 'PropertySearchParams') -> 'PropertySearchParams':
        """Merge de esta instancia, con otra, la prioridad se da a la otra instancia"""
        for key_name in vars(self):
            getattr(self, key_name).merge_with(getattr(other, key_name))