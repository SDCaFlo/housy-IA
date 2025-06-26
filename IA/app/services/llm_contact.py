from botocore.exceptions import ClientError
from app.core.config import BEDROCK_MODEL_ID
from app.core.aws_clients import get_bedrock_client

def call_model(conversation: list, system_prompt: str) -> str:
    """
    Calls the model and gets a response.
    """

    client = get_bedrock_client()

    systemPrompt = [
        {
            "text": system_prompt
        }
    ]

    inference_config = { # all Optional, Invoke parameter names used in this example
        "maxTokens": 250,  # greater than 0, equal or less than 5k (default: dynamic*)
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