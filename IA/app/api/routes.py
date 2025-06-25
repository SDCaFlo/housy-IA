"""✔️ Rol:
Esta carpeta se encarga de definir los endpoints HTTP. Aquí es donde le dices a FastAPI:
Qué rutas estarán disponibles (/chat, /health, /ping, etc.)
Qué funciones se ejecutan cuando llega una solicitud
Qué modelos se usan para entrada/salida"""

# from fastapi import APIRouter
# from app.services.ChatBotEngine import get_response
# from app.models.ChatMessage import ChatMessage

# router = APIRouter()

# @router.post("/chat")
# def chat_endpoint(message: ChatMessage):
#     return get_response(message)