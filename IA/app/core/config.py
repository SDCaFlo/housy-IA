"""✔️ Rol:
Esta carpeta maneja la configuración central del proyecto, como:
Variables de entorno
Configuración de LangChain o Bedrock
Conexiones a servicios (como AWS, Redis, S3)
Logger global
Middlewares generales (CORS, errores, etc.)"""

import os
from dotenv import load_dotenv

if os.getenv("ENV", "local") == "local":
    from dotenv import load_dotenv

    load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
INTENT_DETECTION_MODEL = os.getenv("INTENT_DETECTION_MODEL", "amazon.nova-micro-v1:0")
SUMMARIZE_MODEL = os.getenv("INTENT_DETECTION_MODEL", "amazon.nova-micro-v1:0")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "ChatMessages")
LOCAL_PROFILE_NAME = os.getenv("LOCAL_PROFILE_NAME", "HousyProject")
EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID", "amazon.titan-embed-text-v1")
NER_MODEL_ID = os.getenv("NER_MODE_ID", "amazon.nova-lite-v1:0")
SMALL_TALK_MODEL_ID = os.getenv("SMALL_TALK_MODEL_ID", "amazon.nova-lite-v1:0")
QUERY_USER_MODEL_ID = os.getenv("QUERY_USER_MODEL_ID", "amazon.nova-micro-v1:0")
FAQ_MODEL_ID = os.getenv("FAQ_MODEL_ID", "amazon.nova-micro-v1:0")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "properties")
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD")
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST")
ROUTER_MODEL_ID = os.getenv("ROUTER_MODEL_ID")
OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY")
AURORA_DB_USER = os.getenv('AURORA_DB_USER')
AURORA_DB_PASSWORD = os.getenv('AURORA_DB_PASSWORD')
AURORA_DB_URL = os.getenv('AURORA_DB_URL')

