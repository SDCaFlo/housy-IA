from pydantic import BaseModel, Field
from typing import Any, Optional,List
from enum import Enum
from app.models.PropertyLead import PropertySearchParams

class InputRouter(str, Enum):
    extract = 'extract'
    new_search = 'new_search'
    other = 'other'
    
class ContentTypeMapping(str, Enum):
    """Mapping para tipo de contenido en base al final output"""
    other = 'text'
    query_user = 'text'
    search_properties = 'property_list'

class MyState(BaseModel):
    user_message: str
    message_history: list
    input_lead: PropertySearchParams
    input_state: dict
    current_state_flow: List[str] = []
    new_search_flag: bool = Field(default=None, description='Flag indication a new search. Used for reseting context length')
    input_route_result: Optional[dict] | None = {}
    extract_result: Optional[dict] | None = {}
    lead_route_result: Optional[str] | None = None
    query_user_result: Optional[dict] | None = {}
    search_properties_result: Optional[list] | None = None
    location_verification_result: Optional[dict] | None = {}
    other_result: Optional[str] | None = None
    final_output: Optional[dict] = None