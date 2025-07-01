"""✔️ Rol:
Verificar el funcionamento del embed Titan."""

from fastapi import APIRouter
from app.models.EmbedRequest import EmbedRequest, EmbedResponse
from app.services.embeddings.bedrock_service import embed_text
from fastapi import APIRouter, HTTPException


router = APIRouter()

@router.post("/embed_text", response_model=EmbedResponse)
async def chat_history_request(payload: EmbedRequest):
    try:
        input_message = payload.message
        embed = embed_text(input_message)

        return EmbedResponse(embed=embed)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    

