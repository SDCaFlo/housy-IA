"""Clase para guardar estado de LangGraph.
Puntos de mejora posibles"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from app.models.PropertyLead import PropertySearchParams


class InputRouter(str, Enum):
    extract = "extract"
    new_search = "new_search"
    other = "other"
    small_talk = "small_talk"
    #faq = "faq"

# class InputRouterDescription(str, Enum):
#     extract = Field("extract", description="Para análisis, extracción y/o procesamiento de información específica. Si el cliente se encuentra aportando información o confirmandola.")
#     new_search = Field("new_search", description="Sólo cuando el cliente indica explícitamente que quiere comenzar la búsqueda desde 0 (Borra todo el historial)")
#     other = Field("other", description="Si no se trata de un tema asociado a búsquedas inmobiliarias")
#     small_talk = Field("small_talk", description="Para saludos, cortesías, agradecimientos, despedidas, confirmaciones simples SIN contexto relevante, etc")
#     faq = Field("faq", description="Para preguntas sobre el servicio tales como cobertura, funcionamiento, recomendaciones de servicios, asociados a la búsqueda inmobiliaria.")


route_descriptions = {
    InputRouter.extract: """extract: 
    - Usuario proporciona criterios de búsqueda (ubicación, precio, características)
    - Usuario responde a preguntas con datos específicos
    - Usuario modifica o ajusta criterios existentes
    - Ejemplos: "en San Isidro", "hasta $500k", "con 3 dormitorios", "sí, con jardín"
    """,
    
    InputRouter.new_search: """new_search:
    - Usuario EXPLÍCITAMENTE pide empezar de cero
    - Frases como: "nueva búsqueda", "empezar de nuevo", "olvidar lo anterior", "comenzar otra vez"
    - NO usar para simples cambios de criterios
    """,
    
    InputRouter.small_talk: """small_talk:
    - Saludos: "hola", "buenos días", "qué tal"
    - Despedidas: "chau", "gracias", "hasta luego"
    - Cortesías sin intención: "ok", "entiendo", "perfecto" (SIN contexto previo)
    - NO usar si hay contexto de búsqueda activa
    """,
    
    # InputRouter.faq: """faq:
    # - Preguntas sobre el servicio: "¿qué zonas cubren?", "¿cómo funciona?", "¿cobran comisión?"
    # - Preguntas sobre capacidades del bot
    # - Consultas sobre proceso o políticas
    # """,
    
    InputRouter.other: """other:
    - Temas COMPLETAMENTE fuera del dominio inmobiliario
    - Ejemplos: recetas de cocina, política, deportes, consejos personales
    - NO usar para mensajes ambiguos relacionados con inmuebles
    """
}



class ContentTypeMapping(str, Enum):
    """Mapping para tipo de contenido en base al final output"""

    other = "text"
    query_user = "text"
    search_properties = "property_list"
    small_talk = "text"
    faq_llm = "text"


class MyState(BaseModel):
    user_message: str
    message_history: list
    input_lead: PropertySearchParams
    input_state: dict
    current_state_flow: List[str] = []
    new_search_flag: bool = Field(
        default=None,
        description="Flag indication a new search. Used for reseting context length",
    )
    input_route_result: Optional[dict] | None = {}
    extract_result: Optional[dict] | None = {}
    lead_route_result: Optional[str] | None = None
    query_user_result: Optional[dict] | None = {}
    small_talk_result: Optional[dict] | None = {}
    faq_retrieve_result: Optional[List] | None = [] 
    faq_llm_result: Optional[dict] | None = {}
    search_properties_result: Optional[list] | None = None
    location_verification_result: Optional[dict] | None = {}
    other_result: Optional[str] | None = None
    final_output: Optional[dict] = None
