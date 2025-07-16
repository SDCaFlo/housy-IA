from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Union, Literal, Any


class ChatMessage(BaseModel):
    # clase básica para el input de mensaje
    PK: str
    SK: str
    role: str
    content_type: Literal["text", "property_list"]
    content: Dict[str, Any]
    metadata: Optional[Dict] = None

class UserMessage(BaseModel):
    # clase para nuevo mensaje de cliente
    user_id: str
    conv_id: str
    message: str
    verbose: bool = False
    metadata: Optional[Dict] = None

class ChatResponse(BaseModel):
    # model response in str
    stage: str
    response: Union[str, List, Dict]

class ChatHistoryRequest(BaseModel):
    """History request structure"""
    user_id: str
    conv_id: str
    limit: int = 10
    reverse: bool = False
    verbose: Optional[bool] = False


class ChatHistoryElement(BaseModel):
    """Base element for ChatHistoryResponse"""
    role: str
    content: Dict[str, Any]
    content_type: Literal["text", "property_list"]
    SK: Optional[str] = None
    metadata: Optional[Dict] = None

    class Config:
        exclude_none = True

class ChatHistoryResponse(BaseModel):
    """History response structure"""
    history: List[ChatHistoryElement]

    class Config:
        exclude_none = True