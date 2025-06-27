import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Configura cliente Bedrock Runtime
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
)

MODEL_ID = "amazon.titan-embed-text-v1"

def embed_text(text: str):
    payload = {
        "inputText": text
    }

    response = bedrock.invoke_model(
        body=json.dumps(payload),
        modelId=MODEL_ID,
        accept="application/json",
        contentType="application/json"
    )

    response_body = json.loads(response['body'].read())
    return response_body['embedding']

