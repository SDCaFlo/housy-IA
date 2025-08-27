from fastapi import APIRouter, HTTPException
from app.models.ChatMessage import UserMessage, ChatResponse
from app.services.chatblot_langraph import proccess_chat_turn
#from app.utils.intention_detection import tiene_intencion_busqueda
#from app.services.embeddings.search_opensearch import search_similar_properties


router = APIRouter()

@router.post("/chat")
async def chat_endpoint(payload: UserMessage):
    """
    Endpoint principal del chatbot.

    Recibe un mensaje del usuario, procesa la conversación y retorna la respuesta del asistente,
    junto con los IDs de las propiedades recomendadas si existen.
    """
    try:
        user_message = payload.message
        user_id = payload.user_id
        conv_id = payload.conv_id

        verbose = payload.verbose
        metadata = payload.metadata

        stage, response = proccess_chat_turn(
            user_id=user_id,
            conv_id=conv_id,
            user_message=user_message,
            metadata=metadata,
            verbose=verbose
        )

        return ChatResponse(stage=stage,response=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

