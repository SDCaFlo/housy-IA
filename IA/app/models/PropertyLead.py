"""Estructura para guardar LEADs.
Langchain usa pydanticparser para poder transformar el speech de cliente en esta clase
"""

from pydantic import BaseModel, Field, model_validator, ConfigDict, computed_field
from app.services.embeddings.bedrock_service import embed_text
from typing_extensions import Self
from typing import Optional, List, Generic, TypeVar
from enum import Enum
import logging


class SlotState(str, Enum):
    """Estado del slot.
    - missing: valor faltante
    - pending_validation: pendiente de validación
    - validated: campo validado"""

    MISSING = "missing"
    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"
    VALIDATION_FAILED = "validation_failed"


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


T = TypeVar("T")  # Slot Genérico


class Slot(BaseModel, Generic[T]):
    """Clase genérica para SLOT. Permite tipado flexible."""

    value: Optional[T] = None
    required: bool = False

    def merge_with(self, other: "Slot[T]") -> "Slot[T]":
        if other.value is None:
            return self
        if hasattr(self.value, "merge_with") and hasattr(other.value, "merge_with"):
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
    #lon: Optional[float] = None
    #lat: Optional[float] = None
    geom: Optional[list] = None

    @computed_field
    def state(self) -> SlotState:
        if self.geom is not None:
            if self.geom == [999,]:
                return SlotState.VALIDATION_FAILED
            else:
                return SlotState.VALIDATED
        elif self.value is not None:
            return SlotState.PENDING_VALIDATION
        else:
            return SlotState.MISSING

    def merge_with(self, other: "LocationSlot") -> "LocationSlot":
        if other.value is None:
            return self
        else:
            self.value = other.value
            self.geom = None


class Range(BaseModel, Generic[T]):
    """Rango numérico con mínimo y máximo"""

    model_config = ConfigDict(validate_assignment=True)

    min: Optional[T] = None
    max: Optional[T] = None

    def merge_with(self, other: "Range[T]") -> "Range[T]":
        if other is None:
            return
        if other.min not in [None]:
            self.min = other.min
        if other.max not in [None]:
            self.max = other.max

    @model_validator(mode="after")
    def check_valid_range(self) -> Self:
        if self.min is not None and self.min < 0:
            raise ValueError("model_validator: Negative value")
        if self.max is not None and self.max < 0:
            raise ValueError("model_validator: Negative value")
        if self.max is not None and self.min is not None:
            if self.max < self.min:
                raise ValueError("mode_validator: Invalid range max<min")

        return self


class PropertySearchParams(BaseModel):
    """Esquema para extracción NER"""

    ## Valores requeridos
    property_types: Optional[Slot[List[PropertyType]]] = Field(
        default_factory=lambda: Slot[List[PropertyType]](value=None, required=True),
        description="Objeto Slot que contiene: "
        'value: Lista de tipos de propiedades (Ejemplo: ["departamento", "casa"]), ',
    )

    operation_types: Optional[Slot[OperationType]] = Field(
        default_factory=lambda: Slot[OperationType](value=None, required=True),
        description="Objeto Slot que contiene: "
        'value: Tipo de operacion que el usuario quiere realizar (¿comprar o alquilar?): Ejemplo: "alquiler" "',
    )

    location: Optional[LocationSlot] = Field(
        default_factory=lambda: LocationSlot(value=None, required=True),
        description="Objeto Slot que contiene: "
        'value: Dirección de la propiedad (País, Ciudad, Distrito, Zona). Ejemplo: "Lima, Miraflores"',
    )

    price: Optional[Slot[float]] = Field(
        default_factory=lambda: Slot[float](value=None, required=True),
        description="Objeto Slot que contiene: "
        "value: Precios de referencia de la propiedad en dólares. Ejemplo: 1000.00",
    )

    area: Optional[Slot[float]] = Field(
        default_factory=lambda: Slot[float](value=None, required=False),
        description="Objeto Slot que contiene: "
        "value: Área de la propiedad en metros cuadrados (m2), Ejemplo: 70",
    )

    bedroom_quantity: Optional[Slot[int]] = Field(
        default_factory=lambda: Slot[int](value=None, required=False),
        description="Objeto Slot que contiene: "
        "value: Cantidad de habitaciones deseadas, Ejemplo: 3",
    )

    bathroom_quantity: Optional[Slot[int]] = Field(
        default_factory=lambda: Slot[int](value=None, required=False),
        description="Objeto Slot que contiene: "
        "value: Cantidad de baños deseados, Ejemplo: 2",
    )

    ## Methods

    def merge_with(self, other: "PropertySearchParams") -> "PropertySearchParams":
        """Merge de esta instancia, con otra, la prioridad se da a la otra instancia"""
        for key_name in vars(self):
            getattr(self, key_name).merge_with(getattr(other, key_name))
        return self

    def verify_lead(self) -> bool:
        """Verifica si el objeto cumple lo mínimo requerido para realizar una búsqueda"""
        param: Slot
        for param in vars(self).values():
            if param.required == True and param.state.value in [
                "missing",
                "pending_validation",
                "validation_failed",
            ]:
                return False
        else:
            return True

    def generate_embedding(self) -> list:
        """Genera un embedding de texto para búsqueda semántica"""
        text = ""
        # description_embedding = embed_text(title + " " + desc + " " + location + " " + address)
        if self.location.value:
            text += self.location.value
        # if self.property_types.value: text += " " + " ".join([val.value for val in self.property_types.value])
        # if self.operation_types.value: text += " " + self.operation_types.value.value

        try:
            logging.info("Embedding service: Attempting to embed text")
            text_embedding = embed_text(text)
            return text_embedding
        except Exception as e:
            logging.info(f"Embedding service error: Failed to embed text: {e}")
            return []

    def format_query_instructions(self) -> dict:
        """Returns a list of the missing parameters"""
        missing_values = [
            key
            for key, value in vars(self).items()
            if value.state.value in ["missing", "validation_failed"]
        ]

        query_list = []

        # missing parameters
        for parameter in missing_values:
            text = f"{parameter}: {PropertySearchParams.model_fields.get(parameter).description.strip('Objeto Slot que contiene: value:')}"
            if getattr(self, parameter).required == True:
                query_list.insert(0, "- REQUERIDO!: " + text)
            else:
                query_list.append("- " + text)

        # failed location validation
        if self.location.state.value == "validation_failed":
            location = self.location.value
            query_list.insert(
                0,
                f"- URGENTE!: location: La ubicación {location} no pudo ser validada, solicitar mayor precisión al usuario.",
            )

        if query_list == []:
            output_text = "- No hay valores faltantes"
        else:
            output_text = "\n".join(query_list)

        return output_text

    def to_opensearch_query(
        self, query_size: int = 3, max_distance: int = 5, debug: bool = False
    ):
        """
        Reglas:
            1. Bloques Must: Filtra y suma al score
                - status publicado.
                - operation_type
                - property_types
            2. Bloques Filter: Filtra sin afectar score.
                - max_price
            3. Bloques Should: No filtra, pero beneficia el score si cumple con el requisito
                - Funcion:
                    - RBF: min_price
                    - RBF: bathrooms
                    - RBF: bedrooms
        """
        # bloques must
        must = []

        must.append({"term": {"status": "publicado"}})
        if self.operation_types.value:
            must.append({"term": {"operation_type": self.operation_types.value.value}})
        if self.property_types.value:
            must.append(
                {
                    "terms": {
                        "property_type": [
                            val.value for val in self.property_types.value
                        ]
                    }
                }
            )

        # bloques filter
        filter = []
        # if self.price.value.max:
        #     filter.append({"range": {"price": {"lte" : self.price.value.max}}})

        # geolocalización. Filtro.
        if self.location.value:
            filter.append(
                {
                    "geo_distance": {
                        "distance": f"{max_distance}km",
                        "geolocation": {
                            "lat": self.location.lat,
                            "lon": self.location.lon,
                        },
                    }
                }
            )

        # bloques should
        should = []

        functions = []
        # Funcion de decaimiento por geolocalizacion.
        if self.location.value:
            functions.append(
                {
                    "gauss": {
                        "geolocation": {
                            "origin": {
                                "lat": self.location.lat,
                                "lon": self.location.lon,
                            },
                            "scale": "2km",  # Distancia donde el score empieza a decaer
                            "offset": "0km",  # Distancia sin penalización
                            "decay": 0.5,  # Factor de decaimiento
                        }
                    },
                    "weight": 2.0,  # Peso alto para priorizar cercanía
                }
            )
        # Funcion decaimiento precio
        if self.price.value:
            price_reference = self.price.value
            functions.append(
                {
                    "gauss": {
                        "price": {
                            "origin": price_reference,
                            "scale": max(price_reference * 0.1, 1),
                            "decay": 0.5,
                        }
                    },
                    "weight": 1.0,
                }
            )
        # Funcion decaimiento cantidad de habitaciones
        if self.bedroom_quantity.value:
            functions.append(
                {
                    "gauss": {
                        "space_count_by_type.Dormitorio": {
                            "origin": self.bedroom_quantity.value,
                            "scale": 1,
                            "decay": 0.5,
                        }  # ±1 habitación = decay 0.5
                    },
                    "weight": 1.0,
                }
            )
        # Funcion decaimiento cantidad de baños
        if self.bathroom_quantity.value:
            functions.append(
                {
                    "gauss": {
                        "space_count_by_type.Baño": {
                            "origin": self.bathroom_quantity.value,
                            "scale": 1,
                            "decay": 0.5,
                        }
                    },
                    "weight": 0.8,
                }
            )

        if functions:
            should.append(
                {
                    "function_score": {
                        "query": {"match_all": {}},
                        "functions": functions,
                        "score_mode": "sum",
                    }
                }
            )

        ## Embeding
        embbeding = self.generate_embedding()
        should.append(
            {
                "knn": {
                    "description_embedding": {
                        "vector": embbeding,
                        "k": 100,
                        "boost": 15.0,
                    }
                }
            }
        )

        # location
        should.append(
            {
                "multi_match": {
                    "query": self.location.value,  # Tu texto de búsqueda
                    "fields": ["address", "unified_description", "title", "location"],
                    "boost": 5.0,
                    "type": "most_fields",
                    "fuzziness": "AUTO",
                }
            }
        )

        # query construction
        bool = dict()
        if must:
            bool["must"] = must
        if filter:
            bool["filter"] = filter
        if should:
            bool["should"] = should

        query = {
            "size": query_size,
            "query": {"bool": {**bool, "minimum_should_match": 1}},
        }

        if debug:
            query["explain"] = True  # Explica cómo se calculó cada score
            query["_source"] = True
            query["highlight"] = {"fields": {"description": {}}}

        return query

    def to_opensearch_query_knn_filtered(
        self, query_size: int = 3, debug: bool = False
    ):
        embedding = self.generate_embedding()

        # Filtros esenciales dentro del KNN
        essential_filters = [{"term": {"status": "publicado"}}]
        if self.operation_types.value:
            essential_filters.append(
                {"term": {"operation_type": self.operation_types.value.value}}
            )

        query = {
            "size": query_size,
            "query": {
                "knn": {
                    "description_embedding": {
                        "vector": embedding,
                        "k": 150,
                        "filter": {  # Filtros DENTRO del KNN
                            "bool": {"must": essential_filters}
                        },
                    }
                }
            },
            # Rescoring para características y ubicación textual
            "rescore": [
                {
                    "window_size": min(50, query_size * 10),
                    "query": {
                        "rescore_query": {
                            "bool": {
                                "should": [
                                    # Multi-match ubicación
                                    {
                                        "multi_match": {
                                            "query": self.location.value,
                                            "fields": [
                                                "address^3",
                                                "location^2",
                                                "title^1",
                                                "unified_description^1",
                                            ],
                                            "boost": 5.0,
                                            "type": "most_fields",
                                            "fuzziness": "AUTO",
                                        }
                                    },
                                    # Function score características
                                    self._build_function_score_rescore(),
                                ]
                            }
                        },
                        "query_weight": 2.0,  # KNN tiene peso 2
                        "rescore_query_weight": 1.0,  # Rescoring tiene peso 1
                    },
                }
            ],
        }

        return query

    def _build_function_score_rescore(self):
        functions = []

        # Tus funciones existentes pero con pesos ajustados para rescoring
        if self.price.value:
            price_reference = self.price.value
            functions.append(
                {
                    "gauss": {
                        "price": {
                            "origin": price_reference,
                            "scale": max(price_reference * 0.1, 1),
                            "decay": 0.5,
                        }
                    },
                    "weight": 25.0,  # Peso reducido en rescoring
                }
            )

        if self.bedroom_quantity.value:
            functions.append(
                {
                    "gauss": {
                        "space_count_by_type.Dormitorio": {
                            "origin": self.bedroom_quantity.value,
                            "scale": 1,
                            "decay": 0.5,
                        }
                    },
                    "weight": 5.0,
                }
            )

        if self.bathroom_quantity.value:
            functions.append(
                {
                    "gauss": {
                        "space_count_by_type.Baño": {
                            "origin": self.bathroom_quantity.value,
                            "scale": 1,
                            "decay": 0.5,
                        }
                    },
                    "weight": 5.0,
                }
            )

        if functions:
            return {
                "function_score": {
                    "query": {"match_all": {}},
                    "functions": functions,
                    "score_mode": "sum",
                }
            }
        else:
            return {"match_all": {}}

    ## utils
    @classmethod
    def generate_valid_lead(cls):
        return PropertySearchParams(
            property_types={"value": ["departamento", "casa"]},
            operation_types={"value": "alquiler"},
            location={"value": "Ate"},
            price={"value": 1500},
            area={"value": 50},
            bedroom_quantity={"value": 2},
            bathroom_quantity={"value": 1},
        )

    @classmethod
    def generate_invalid_lead(cls):
        return PropertySearchParams(
            property_types={"value": ["departamento"]},
            location={"value": "Los Olivos"},
            area={"value": 50},
        )

    @classmethod
    def generate_example_lead_str(cls, full: bool = True):
        """To use with LLM prompting"""
        import json

        if full == True:
            lead = PropertySearchParams.generate_valid_lead()
        else:
            lead = PropertySearchParams()
        lead_dict = json.loads(json.dumps(lead.model_dump()))
        for item in lead_dict.values():
            item.pop("required")
            item.pop("state")
        return json.dumps(lead_dict)

    ##### Test #####
    def test_query(
        self, query_size: int = 3, max_distance: int = 5, debug: bool = False
        ):

        # bloques must
        must = []

        must.append({"term": {"status": "test"}})
        if self.operation_types.value:
            must.append({"term": {"operation_type": self.operation_types.value.value}})
        if self.property_types.value:
            must.append(
                {
                    "terms": {
                        "property_type": [
                            val.value for val in self.property_types.value
                        ]
                    }
                }
            )

        # bloques filter
        filter = []
        # if self.price.value.max:
        #     filter.append({"range": {"price": {"lte" : self.price.value.max}}})

        # geolocalización. Filtro.
        if self.location.value:
            filter.append(
                {
                    "geo_distance": {
                        "distance": f"{max_distance}km",
                        "geolocation": {
                            "lat": self.location.lat,
                            "lon": self.location.lon,
                        },
                    }
                }
            )

        # bloques should
        should = []

        functions = []
        # Funcion de decaimiento por geolocalizacion.
        if self.location.value:
            functions.append(
                {
                    "gauss": {
                        "geolocation": {
                            "origin": {
                                "lat": self.location.lat,
                                "lon": self.location.lon,
                            },
                            "scale": "2km",  # Distancia donde el score empieza a decaer
                            "offset": "0km",  # Distancia sin penalización
                            "decay": 0.5,  # Factor de decaimiento
                        }
                    },
                    "weight": 2.0,  # Peso alto para priorizar cercanía
                }
            )
        # Funcion decaimiento precio
        # if self.price.value:
        #     price_reference = self.price.value
        #     functions.append(
        #         {
        #             "gauss": {
        #                 "price": {
        #                     "origin": price_reference,
        #                     "scale": max(price_reference * 0.1, 1),
        #                     "decay": 0.5,
        #                 }
        #             },
        #             "weight": 1.0,
        #         }
        #     )
        # Funcion decaimiento cantidad de habitaciones
        # if self.bedroom_quantity.value:
        #     functions.append(
        #         {
        #             "gauss": {
        #                 "space_count_by_type.Dormitorio": {
        #                     "origin": self.bedroom_quantity.value,
        #                     "scale": 1,
        #                     "decay": 0.5,
        #                 }  # ±1 habitación = decay 0.5
        #             },
        #             "weight": 1.0,
        #         }
        #     )
        # # Funcion decaimiento cantidad de baños
        # if self.bathroom_quantity.value:
        #     functions.append(
        #         {
        #             "gauss": {
        #                 "space_count_by_type.Baño": {
        #                     "origin": self.bathroom_quantity.value,
        #                     "scale": 1,
        #                     "decay": 0.5,
        #                 }
        #             },
        #             "weight": 0.8,
        #         }
        #     )

        if functions:
            should.append(
                {
                    "function_score": {
                        "query": {"match_all": {}},
                        "functions": functions,
                        "score_mode": "sum",
                    }
                }
            )

        # ## Embeding
        # embbeding = self.generate_embedding()
        # should.append(
        #     {
        #         "knn": {
        #             "description_embedding": {
        #                 "vector": embbeding,
        #                 "k": 100,
        #                 "boost": 15.0,
        #             }
        #         }
        #     }
        # )

        # # location
        # should.append(
        #     {
        #         "multi_match": {
        #             "query": self.location.value,  # Tu texto de búsqueda
        #             "fields": ["address", "unified_description", "title", "location"],
        #             "boost": 5.0,
        #             "type": "most_fields",
        #             "fuzziness": "AUTO",
        #         }
        #     }
        # )

        # query construction
        bool = dict()
        if must:
            bool["must"] = must
        if filter:
            bool["filter"] = filter
        if should:
            bool["should"] = should

        query = {
            "size": query_size,
            "query": {"bool": {**bool, "minimum_should_match": 1}},
        }

        if debug:
            query["explain"] = True  # Explica cómo se calculó cada score
            query["_source"] = True
            query["highlight"] = {"fields": {"description": {}}}

        return query