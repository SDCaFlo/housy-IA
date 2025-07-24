### Logic an utilities for all stages ###
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.aws_clients import get_langchain_bedrock_client
from app.core.config import SUMMARIZE_MODEL


SUMMARIZE_PROMPT = """
Eres un asistente especializado en bienes raíces. Tu tarea es resumir las necesidades actuales del cliente basándote en el historial completo de la conversación.

✅ Si el cliente cambió de opinión o corrigió algún dato durante la conversación, incluye **solo la versión más reciente de cada necesidad** (por ejemplo: ubicación, tipo de propiedad, intención de compra o alquiler, etc.).
📌 No menciones los cambios previos ni el historial del diálogo. Solo entrega el resultado final como una **oración breve y clara en lenguaje natural**.
❗No completes campos por inferencia.
📌 Si el cliente no brinda información válida, no inventemos y devolvamos un texto indicando que no se tiene mayores detalles.

Responde únicamente con ese resumen, sin encabezados, explicaciones ni listas.
"""

def summarize_conversation(conversation)->str:
    """Llamamos al modelo de BEDROCK para resumir"""
    conversation_chat_history = ' '.join([ message['content'][0]['text']for message in conversation ])

    chat_summary_prompt = [
        SystemMessage(content=SUMMARIZE_PROMPT),
        HumanMessage(content=conversation_chat_history)
    ]

    chat = get_langchain_bedrock_client(SUMMARIZE_MODEL)
    response = chat.invoke(chat_summary_prompt)

    return response.content

def get_chat_stage_metadata(latest_messages):
    for msg in reversed(latest_messages):
        try:
            metadata = msg.get("metadata", {})
            if isinstance(metadata, dict) and "stage" in metadata:
                return metadata["stage"]
        except Exception:
            continue
    return "extract"


def get_model_message(stage, response):
    model_message = ""
    try:
        match stage:
            case "extract":
                model_message = response["model_response"]
            case "recommend":
                model_message = str(response)
            case _:
                pass
    except Exception as e:
        model_message = f"error matching message: {e}"
    
    return model_message

