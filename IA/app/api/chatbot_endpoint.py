"""✔️ Rol:
Esta carpeta se encarga de definir los endpoints HTTP. Aquí es donde le dices a FastAPI:
Qué rutas estarán disponibles (/chat, /health, /ping, etc.)
Qué funciones se ejecutan cuando llega una solicitud
Qué modelos se usan para entrada/salida"""

from fastapi import APIRouter, HTTPException
from app.models.ChatMessage import UserMessage, ChatResponse
from app.services.chatbot_engine import proccess_chat_turn
from app.utils.intention_detection import tiene_intencion_busqueda
from app.services.embeddings.search_opensearch import search_similar_properties
from app.services.embeddings.bedrock_service import embed_text

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: UserMessage):
    try:
        message = payload.message
        user_id = payload.user_id
        conv_id = payload.conv_id

        response = proccess_chat_turn(
            user_id=user_id,
            conv_id=conv_id,
            message=message
        )

        return ChatResponse(output=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))