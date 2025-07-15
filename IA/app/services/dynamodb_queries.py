from datetime import datetime, timezone
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer
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
        ScanIndexForward=False,  # orden descendente
        Limit=limit
        )   
    return response


### Writing Data to Dynamodb

def write_message(dynamodb, table_name: str, serialized_item):
    dynamodb.put_item(
        TableName = table_name,
        Item= serialized_item)
    return None
    
def message_wrapper(PK:str , message:str , role: str, metadata: dict):
    """Converts Message into JSON format"""
    format_dict = {'PK': PK,
        'SK': 'TIMESTAMP#'+get_current_timestamp(),
        'message': message,
        'role': role,
        'metadata': metadata
        }
    return format_dict

def serialize_item(model: ChatMessage):
    serializer = TypeSerializer()
    serialized_item = {k: serializer.serialize(v) for k, v in model.model_dump().items()}
    return serialized_item


def serialize_message(message, PK, role, metadata):
    message_dict = message_wrapper(PK, message, role, metadata)
    return serialize_item(ChatMessage(**message_dict))
    message_dict = message_wrapper(PK, message, role, model)
    message_dict['metadata'] = base_metadata

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
        # Metadata opcional para debug o futuro uso
        if 'metadata' in item:
            message_entry['metadata'] = {k: v.get('S', None) or v.get('N', None) for k, v in item['metadata']['M'].items()}
        message_log.append(message_entry)
    return message_log


def get_current_timestamp():
    """Formato utilizado para el timestamp"""
    output = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    return output

def get_metadata(raw_messages):
    deserializer = TypeDeserializer()
    metadata_list = []
    for item in raw_messages['Items'][::-1]:
        deserialized_item =  { k: deserializer.deserialize(v) for k, v in item.items()}
        metadata_list.append(deserialized_item['metadata'])
    return metadata_list
