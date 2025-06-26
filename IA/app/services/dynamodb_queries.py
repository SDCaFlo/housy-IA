
from datetime import datetime, timezone
from boto3.dynamodb.types import TypeSerializer
from app.models.ChatMessage import ChatMessage


### Return messages from Dynamodb ###

def get_all_messages(dynamodb , primary_key: str):
    "Funcion para retornar todos los mensajes, brindando un primary Key."
    "Se debe pasar la session o cliente como el parámetro 'dynamodb'"

    response = dynamodb.query(
        TableName = 'ChatMessages',
        KeyConditionExpression = 'PK = :pk_val',
        ExpressionAttributeValues = {
            ':pk_val' : {'S' : primary_key}
            },
        ScanIndexForward=False
        )
    return response

def get_latests_messages(dynamodb , primary_key: str, limit: int = 2):
    "Funcion para retornar todos los ultimos 10 mensajes, brindando un primary Key."
    "Se debe pasar la session o cliente como el parámetro 'dynamodb'"

    response = dynamodb.query(
        TableName = 'ChatMessages',
        KeyConditionExpression = 'PK = :pk_val',
        ExpressionAttributeValues = {
            ':pk_val' : {'S' : primary_key}
            },
        ScanIndexForward=False,  # orden ascendente
        Limit=limit
        )   
    return response


### Writing Data to Dynamodb

def write_message(dynamodb, table_name: str, serialized_item):
    dynamodb.put_item(
        TableName = table_name,
        Item= serialized_item)
    return None
    
def message_wrapper(PK:str , message:str , role: str, model):
    """Converts Message into JSON format"""
    format_dict = {'PK': PK,
        'SK': 'TIMESTAMP#'+get_current_timestamp(),
        'message': message,
        'role': role,
        'metadata': {
            'model': model,
            'source': 'test'
            }
        }
    return format_dict

def serialize_item(model: ChatMessage):
    serializer = TypeSerializer()
    serialized_item = {k: serializer.serialize(v) for k, v in model.model_dump().items()}
    return serialized_item

def serialize_message(message, PK, role, model: str = "unspecified"):
    message_dict = message_wrapper(PK, message, role, model)
    return serialize_item(ChatMessage(**message_dict))





### Aux
def response_to_conversation(response):
    """Convierte los mensajes en una conversación bedrock"""
    message_log = []
    for item in response['Items'][::-1]:
        message_entry = {
            'role': item['role']['S'],
            'content': [{"text": item['message']['S']}]
        }
        message_log.append(message_entry)
    return message_log


def get_current_timestamp():
    """Formato utilizado para el timestamp"""
    output = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    return output


