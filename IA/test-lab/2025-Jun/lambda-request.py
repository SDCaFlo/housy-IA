import requests
import json
import urllib.parse


lambda_url = 'https://atwkp4dv3iy57mpwdplovzad5y0ifjmj.lambda-url.us-east-1.on.aws/'
local_url = 'http://localhost:9000/2015-03-31/functions/function/invocations'

def build_event(method="GET", path="/test", body=None, query=None):
    raw_query = urllib.parse.urlencode(query or {})
    return {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": "/test",
        "rawQueryString": raw_query,
        "headers": {
            "Content-Type": "application/json"
        },
        "requestContext": {
            "http": {
                "method": method,
                "path": path,
                "sourceIp": "127.0.0.1",  # ✅ agrega esto
                "userAgent": "custom-test-client"  # (opcional, pero válido)
            }
        },
        "body": json.dumps(body) if body else None,
        "isBase64Encoded": False
    }

# ejemplo solicitudes
event = build_event(
    method="POST",
    path="/chatbot/chat",
    body={
        "user_id": "u123",
        "conv_id": "c456",
        "message": "Hola, soy un test desde terminal"
    }
)


res = requests.post(lambda_url, json=event)
print("Status:", res.status_code)
print("Body:", res.text)
