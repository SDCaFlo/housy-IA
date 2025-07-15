# IA/app/services/llm_contact.py

import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
)

def call_model(messages, system_prompt=None):
    """
    messages: lista de {"role": "user"|"assistant", "content": str}
    system_prompt: lista de {"text": str}
    """
    payload = {"messages": messages}
    if system_prompt:
        payload["system"] = system_prompt  # ahora cada item debe tener "text"

    print("🔧 Payload Bedrock:", json.dumps(payload, indent=2))

    response = client.invoke_model(
        modelId=os.getenv("BEDROCK_MODEL_ID"),
        body=json.dumps(payload),
        contentType="application/json",
        accept="application/json"
    )

    body = json.loads(response["body"].read())
    return body["content"][0]["text"]
