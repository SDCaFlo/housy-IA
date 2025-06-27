import os
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth(
    os.getenv("OPENSEARCH_USERNAME"),
    os.getenv("OPENSEARCH_PASSWORD")
)

client = OpenSearch(
    hosts=[os.getenv("OPENSEARCH_HOST")],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)
