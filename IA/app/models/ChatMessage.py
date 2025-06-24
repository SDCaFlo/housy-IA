from pydantic import BaseModel, Field
from typing import Optional, Dict


class ChatMessage(BaseModel):
    # clase básica para el input de mensaje
    PK: str
    SK: str
    role: str
    message: str
    metadata: Optional[Dict] = None