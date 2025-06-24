
from datetime import datetime, timezone
from boto3.dynamodb.types import TypeSerializer
from app.models.ChatMessage import ChatMessage



def get_all_messages(dynamodb , primary_key: str):
    "Funcion para retornar todos los mensajes, brindando un primary Key."
    "Se debe pasar la session o cliente como el parámetro 'dynamodb'"

    response = dynamodb.query(
    TableName = 'ChatMessages',
    KeyConditionExpression = 'PK = :pk_val',
    ExpressionAttributeValues = {
        ':pk_val' : {'S' : primary_key}
        }
    )
    return response

def get_latests_messages(dynamodb , primary_key: str):
    "Funcion para retornar todos los ultimos 10 mensajes, brindando un primary Key."
    "Se debe pasar la session o cliente como el parámetro 'dynamodb'"

    response = dynamodb.query(
        TableName = 'ChatMessages',
        KeyConditionExpression = 'PK = :pk_val',
        ExpressionAttributeValues = {
            ':pk_val' : {'S' : primary_key}
            },
        ScanIndexForward=True,  # orden ascendente
        Limit=10
        )   
    return response

def response_to_list(response):
    """Convierte los mensajes en una lista"""
    message_log = []
    for item in response['Items']:
        message_entry = {
            'role': item['role']['S'],
            'message': item['message']['S']
        }
        message_log.append(message_entry)
    return message_log

def write_message(dynamodb, table_name: str, serialized_item):
    dynamodb.put_item(
        TableName = table_name,
        Item= serialized_item)
    
def serialize_item(model: ChatMessage):
    serializer = TypeSerializer()
    serialized_item = {k: serializer.serialize(v) for k, v in model.model_dump().items()}
    return serialized_item

def get_current_timestamp():
    output = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    return output