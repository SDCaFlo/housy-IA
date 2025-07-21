from fastapi import APIRouter, HTTPException
from app.models.ChatMessage import ChatHistoryRequest, ChatHistoryResponse
from app.services.dynamodb_queries import get_latests_messages, format_messages

router = APIRouter()

@router.post("/message_history", response_model=ChatHistoryResponse, response_model_exclude_none=True)
async def chat_history_request(payload: ChatHistoryRequest):
    """
    Recupera los últimos mensajes de una conversación por usuario y conversación.
    """
    try:
        primary_key = "USER#" + payload.user_id + "#CONV#" + payload.conv_id
        raw_conversation = get_latests_messages(primary_key, payload.limit, )
        formatted_conversation = format_messages(raw_conversation, payload.verbose)

        if payload.reverse == True:
            return ChatHistoryResponse(history=formatted_conversation[::-1])
        return ChatHistoryResponse(history=formatted_conversation)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al recuperar historial: {str(e)}")
