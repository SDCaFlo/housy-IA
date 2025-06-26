"""✔️ Rol:
Esta carpeta se encarga de definir los endpoints HTTP. Aquí es donde le dices a FastAPI:
Qué rutas estarán disponibles (/chat, /health, /ping, etc.)
Qué funciones se ejecutan cuando llega una solicitud
Qué modelos se usan para entrada/salida"""

from fastapi import APIRouter
from app.models.ChatMessage import UserMessage, ChatResponse
from app.services.chatbot_engine import proccess_chat_turn
from fastapi import APIRouter, HTTPException


router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: UserMessage):
    try:
        response = proccess_chat_turn(
            user_id = payload.user_id,
            conv_id = payload.conv_id,
            message = payload.message
        )
        return ChatResponse(output=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    

