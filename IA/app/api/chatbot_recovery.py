"""✔️ Rol:
Recuperar Chats o temas asociados al chat."""

from fastapi import APIRouter
from app.models.ChatMessage import ChatHistoryRequest, ChatHistoryResponse
from app.services.chatbot_engine import format_conversation
from app.services.dynamodb_queries import get_latests_messages
from app.core.aws_clients import get_dynamodb_client
from fastapi import APIRouter, HTTPException


router = APIRouter()

@router.post("/message_history", response_model=ChatHistoryResponse)
async def chat_history_request(payload: ChatHistoryRequest):
    try:
        dynamodb = get_dynamodb_client() 
        primary_key = "USER#" + payload.user_id + "#CONV#" + payload.conv_id
        raw_conversation = get_latests_messages(dynamodb, 
                                                primary_key, 
                                                payload.limit 
            )
        formatted_conversation = format_conversation(raw_conversation)

        return ChatHistoryResponse(history=formatted_conversation)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    

