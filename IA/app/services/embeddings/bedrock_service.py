# IA/app/services/embeddings/bedrock_service.py
import os
import json
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("EMBED_MODEL_ID", "amazon.titan-embed-text-v1")

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

def embed_text(text: str) -> list[float]:
    payload = {"inputText": text}
    try:
        resp = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(payload),
            accept="application/json",
            contentType="application/json"
        )
        body = json.loads(resp["body"].read())
        return body.get("embedding") or body.get("results", [{}])[0].get("embedding")
    except (BotoCoreError, ClientError) as e:
        logging.error(f"Error embedding text: {e}")
        return []
