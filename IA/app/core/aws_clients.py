# codigo para manejo de clientes de aws.
import os
import boto3
from app.core.config import AWS_REGION
from mypy_boto3_bedrock_runtime import BedrockRuntimeClient


def get_boto3_session():
    """Logica para discernir el entorno y cargar el perfil"""
    env = os.getenv("ENV", "local")
    if env == "local":
        from app.core.config import LOCAL_PROFILE_NAME

        return boto3.Session(profile_name=LOCAL_PROFILE_NAME)
    return boto3.Session()


def get_embed_client():
    session = get_boto3_session()
    return session.client("bedrock-runtime", region_name=AWS_REGION)


def get_dynamodb_client() -> BedrockRuntimeClient:
    session = get_boto3_session()
    return session.client("dynamodb", region_name=AWS_REGION)


def get_bedrock_client():
    session = get_boto3_session()
    return session.client("bedrock-runtime", region_name=AWS_REGION)


def get_s3_client():
    session = get_boto3_session()
    return session.client("s3", region_name=AWS_REGION)


def get_opensearch_client():
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from requests.auth import HTTPBasicAuth
    from app.core.config import OPENSEARCH_USER
    from app.core.config import OPENSEARCH_PASSWORD
    from app.core.config import OPENSEARCH_HOST

    auth = HTTPBasicAuth(OPENSEARCH_USER, OPENSEARCH_PASSWORD)

    client = OpenSearch(
        hosts=OPENSEARCH_HOST,
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )
    return client


def get_langchain_bedrock_client(
    model_id, max_tokens: int = 250, temperature: float = 0.6, top_p: float = 0.6
):
    """Sets up langchain bedrock client"""
    from langchain_aws.chat_models.bedrock_converse import ChatBedrockConverse

    client = get_bedrock_client()

    # client config
    chat = ChatBedrockConverse(
        client=client,
        model=model_id,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
    )
    return chat
