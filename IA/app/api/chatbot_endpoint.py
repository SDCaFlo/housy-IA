"""✔️ Rol:
Esta carpeta se encarga de definir los endpoints HTTP. Aquí es donde le dices a FastAPI:
Qué rutas estarán disponibles (/chat, /health, /ping, etc.)
Qué funciones se ejecutan cuando llega una solicitud
Qué modelos se usan para entrada/salida"""

from fastapi import APIRouter, HTTPException
from app.models.ChatMessage import UserMessage
from app.services.chatbot_engine import proccess_chat_turn

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(payload: UserMessage):
    """
    Endpoint principal del chatbot.

    Recibe un mensaje del usuario, procesa la conversación y retorna la respuesta del asistente,
    junto con los IDs de las propiedades recomendadas si existen.
    """
    try:
        response = proccess_chat_turn(
            user_id=payload.user_id,
            conv_id=payload.conv_id,
            message=payload.message
        )

        return {
            "stage": response.get("stage"),
            "data": {
                "message": response["data"].get("message"),
                "ids": response["data"].get("ids", [])
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
