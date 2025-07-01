import os
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Cargar variables del entorno
load_dotenv()

# Verifica valor cargado
print("🔍 HOST OPENSEARCH:", os.getenv("OPENSEARCH_HOST"))

auth = HTTPBasicAuth(
    os.getenv("OPENSEARCH_USERNAME"),
    os.getenv("OPENSEARCH_PASSWORD")
)

client = OpenSearch(
    hosts=[{
        "host": os.getenv("OPENSEARCH_HOST"),
        "port": 443
    }],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)


"""
# Cargar variables desde el archivo .env
load_dotenv()

OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST")
OPENSEARCH_USER = os.getenv("OPENSEARCH_USERNAME")
OPENSEARCH_PASS = os.getenv("OPENSEARCH_PASSWORD")

# Crear cliente OpenSearch
client = OpenSearch(
    hosts=[{'host': OPENSEARCH_HOST, 'port': 443}],
    http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS),
    use_ssl=True,
    verify_certs=True
)"""
