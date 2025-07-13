from fastapi import APIRouter, HTTPException
from app.models.ChatMessage import ChatHistoryRequest, ChatHistoryResponse
from app.services.chatbot_engine import format_conversation
from app.services.dynamodb_queries import get_latests_messages
from app.core.aws_clients import get_dynamodb_client

router = APIRouter()

@router.post("/message_history", response_model=ChatHistoryResponse)
async def chat_history_request(payload: ChatHistoryRequest):
    """
    Recupera los últimos mensajes de una conversación por usuario y conversación.
    """
    try:
        dynamodb = get_dynamodb_client()
        primary_key = f"USER#{payload.user_id}#CONV#{payload.conv_id}"

        raw_conversation = get_latests_messages(
            dynamodb, primary_key, payload.limit
        )
        formatted_conversation = format_conversation(raw_conversation)

        return ChatHistoryResponse(history=formatted_conversation)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al recuperar historial: {str(e)}")
