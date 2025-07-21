from datetime import datetime, timezone
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer
from app.models.ChatMessage import ChatMessage, ChatHistoryElement, ChatHistoryResponse
from app.core.aws_clients import get_dynamodb_client
### Return messages from Dynamodb ###

def get_all_messages(primary_key: str):
    "Funcion para retornar todos los mensajes, brindando un primary Key."
    "Se debe pasar la session o cliente como el parámetro 'dynamodb'"

    response = get_dynamodb_client().query(
        TableName = 'ChatMessages',
        KeyConditionExpression = 'PK = :pk_val',
        ExpressionAttributeValues = {
            ':pk_val' : {'S' : primary_key}
            },
        ScanIndexForward=False
        )
    return response

def get_latests_messages(primary_key: str, limit: int = 2, order: bool=True):
    "Funcion para retornar todos los ultimos 10 mensajes, brindando un primary Key."
    "Se debe pasar la session o cliente como el parámetro 'dynamodb'"

    if limit < 1:
        limit = 1

    response = get_dynamodb_client().query(
        TableName = 'ChatMessages',
        KeyConditionExpression = 'PK = :pk_val',
        ExpressionAttributeValues = {
            ':pk_val' : {'S' : primary_key}
            },
        ScanIndexForward=False,  # orden descendente, últimos mensajes
        Limit=limit
        )
    
    if order==True:
        response['Items'] = response.get('Items')[::-1]

    return response


### Writing Data to Dynamodb

def write_message(table_name: str, serialized_item):
    get_dynamodb_client().put_item(
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

def message_wrapper_flex(message_dict: dict):
    """Funcion de empaquetado flexible"""
    return {
        **message_dict,
        'SK': 'TIMESTAMP#'+get_current_timestamp()
    }



def serialize_item(model: ChatMessage):
    from decimal import Decimal

    def convert_floats_to_decimal(obj):
        if isinstance(obj, float):
            return Decimal(str(obj))  # Nunca uses Decimal(float), siempre convierte a str primero
        elif isinstance(obj, list):
            return [convert_floats_to_decimal(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
        else:
            return obj
    
    raw_dict = model.model_dump()
    clean_dict = convert_floats_to_decimal(raw_dict)
        
    serializer = TypeSerializer()
    serialized_item = {k: serializer.serialize(v) for k, v in clean_dict.items()}
    return serialized_item


def serialize_message(message, PK, role, metadata):
    message_dict = message_wrapper(PK, message, role, metadata)
    return serialize_item(ChatMessage(**message_dict))

### Aux



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

def deserialize_item(dynamo_object: dict) -> dict:
    """Deserializador de items en formato diccionario / JSON"""
    deserializer = TypeDeserializer()
    return {
        k: deserializer.deserialize(v) 
        for k, v in dynamo_object.items()
    }


def format_messages(raw_conversation, verbose: bool):
    """Formats message for output in history endpoint"""
    message_list = []
    for raw_item in raw_conversation.get('Items'):
        item = deserialize_item(raw_item)
        if verbose == False:
            item.pop('SK')
            item.pop('metadata')
        message_list.append(ChatHistoryElement(**item))
    
    return message_list
