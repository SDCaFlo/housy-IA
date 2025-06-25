
from typing import List, Dict
from app.services.dynamodb_queries import get_latests_messages, write_message, response_to_list
from app.models.ChatMessage import ChatMessage

# funciones como
# get_response
# get_context
# create_response
# user_chat

def build_history_prompt(messages: List[Dict]) -> str:
    """Creamos un prompt con el historial de mensajes para dar contexto"""
    history_prompt = ""

    if len(messages)>0:
        for message in messages:
            role = message['role']
            text = message['message']
            history_prompt += f"{role}: {text}\n"

    return history_prompt

def call_model(conversation: list, system_prompt: str) -> str:
    from botocore.exceptions import ClientError
    from app.core.config import BEDROCK_MODEL_ID
    from app.core.aws_clients import get_bedrock_client
    client = get_bedrock_client()

    systemPrompt = [
        {
            "text": system_prompt
        }
    ]

    inference_config = { # all Optional, Invoke parameter names used in this example
        "maxTokens": 50,  # greater than 0, equal or less than 5k (default: dynamic*)
        "temperature": 0.7, 
        "topP": 0.1, 
        #"topK": int, // 0 or greater (default: 50)
        #"stopSequences": [string]
    }

    try:
        # Send the message to the model, using a basic inference configuration.
        response = client.converse(
            system=systemPrompt,
            modelId=BEDROCK_MODEL_ID,
            messages=conversation,
            inferenceConfig=inference_config
        )
  
        response_text = response["output"]["message"]["content"][0]["text"]

    except (ClientError, Exception) as e:
        error = f"ERROR: Can't invoke '{BEDROCK_MODEL_ID}'. Reason: {e}"
        return error
    
    return response_text


