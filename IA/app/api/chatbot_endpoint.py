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
from fastapi import APIRouter, HTTPException
from app.models.ChatMessage import UserMessage, ChatResponse
from app.services.chatbot_engine import proccess_chat_turn

router = APIRouter()

@router.post("/chat")  # <-- aquí quitas response_model=ChatResponse
async def chat_endpoint(payload: UserMessage):
    """
    Endpoint principal del chatbot.

    Recibe un mensaje del usuario, procesa la conversación y retorna la respuesta del asistente.
    """
    try:
        message = payload.message
        user_id = payload.user_id
        conv_id = payload.conv_id

        # Procesar el turno del chat
        response = proccess_chat_turn(user_id=user_id, conv_id=conv_id, message=message)

        return response

    except Exception as e:
        # Devuelve error 500 si algo falla
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
