
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
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "ChatMessages")
LOCAL_PROFILE_NAME=os.getenv("LOCAL_PROFILE_NAME", "HousyProject")
EMBED_MODEL_ID=os.getenv("EMBED_MODEL_ID", "amazon.titan-embed-text-v1")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "properties")
OPENSEARCH_USER= os.getenv("OPENSEARCH_USER")
OPENSEARCH_PASSWORD= os.getenv("OPENSEARCH_PASSWORD")
OPENSEARCH_HOST=os.getenv("OPENSEARCH_HOST")
