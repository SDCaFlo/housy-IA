from pydantic import BaseModel
from typing import List


class EmbedRequest(BaseModel):
    # clase básica para el input de mensaje
    message: str

class EmbedResponse(BaseModel):
    # clase básica para el input de mensaje
    embed: List