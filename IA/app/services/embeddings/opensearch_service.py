# IA/app/services/embeddings/opensearch_service.py
import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests.auth import HTTPBasicAuth
import logging

load_dotenv()

HOST = os.getenv("OPENSEARCH_HOST")
USER = os.getenv("OPENSEARCH_USERNAME")
PASS = os.getenv("OPENSEARCH_PASSWORD")

if not (HOST and USER and PASS):
    logging.error("Faltan credenciales de OpenSearch en el .env")

client = OpenSearch(
    hosts=[{"host": HOST, "port": 443}],
    http_auth=HTTPBasicAuth(USER, PASS),
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)
