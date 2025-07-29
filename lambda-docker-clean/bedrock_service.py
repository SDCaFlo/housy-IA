import os
import json
import boto3
from botocore.exceptions import ClientError

def embed_text(text: str):
    # Cliente Bedrock directo
    client = boto3.client('bedrock-runtime')
    
    # Modelo ID desde variable de entorno
    model_id = os.environ.get('EMBED_MODEL_ID', 'amazon.titan-embed-text-v1')
    
    payload = {
        "inputText": text
    }

    try:
        response = client.invoke_model(
            body=json.dumps(payload),
            modelId=model_id,
            accept="application/json",
            contentType="application/json"
        )

        response_body = json.loads(response['body'].read())
        return response_body['embedding']
    
    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        return None
