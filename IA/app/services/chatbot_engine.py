
from typing import List
from app.models.ChatMessage import ChatHistoryElement
from app.core.config import DYNAMODB_TABLE
from boto3.dynamodb.types import TypeDeserializer


# funciones como
# get_response
# get_context
# create_response
# user_chat

def format_message(message: str, role: str="user"):
    """Formatea el mensaje del cliente para que devuelva 
    estructura de mensaje para bedrock"""
    return {'role': role, 'content': [{'text': message}]}

def format_conversation(conversation_history, verbose: bool=False):
    """Formats the output for chat history recovery"""
    formatted_history = []
    if verbose==False:
        for item in conversation_history['Items'][::-1]:
            text = item['message']['S']
            role = item['role']['S']
            formatted_history.append({'role': role, 'message': text})
    elif verbose==True:
        for item in conversation_history['Items'][::-1]:
            text = item['message']['S']
            role = item['role']['S']
            timestamp = item['SK']['S']
            metadata = item['metadata']['M']
            formatted_history.append({'role': role, 'message': text, 'timestamp': timestamp, 'metadata': metadata})
    return formatted_history


def format_conversation_2(conversation_history, verbose=False):
    """Formats the output for chat history recovery
    version 2: Using deserializer"""
    formatted_history = []
    deserializer = TypeDeserializer()
    for item in conversation_history['Items'][::-1]:
        deserialized_item =  { k: deserializer.deserialize(v) for k, v in item.items()}
        if verbose==False:
            del deserialized_item['metadata']
            del deserialized_item['SK']
        formatted_history.append(ChatHistoryElement(**deserialized_item))

    return formatted_history

def get_chat_stage(conversation):
    pass # pending logic for stage definition
    return 1

def proccess_chat_turn(user_id: str, conv_id:str, message:str, metadata:dict = {}):
    """Logica por stages para el procesamiento de chats"""
    primary_key = "USER#"+user_id+"#CONV#"+conv_id
    #1. Get Chat History
    ''' - recuperamos contexto
        - anexamos nuevo mensaje
        - guardamos nuevo mensaje
    '''
    from app.core.aws_clients import get_dynamodb_client
    from app.services.dynamodb_queries import get_latests_messages, response_to_conversation, serialize_message, write_message

    dynamodb = get_dynamodb_client() # creacion sesion
    latest_messages = get_latests_messages(dynamodb, primary_key, limit=10)
    latest_conversation = response_to_conversation(latest_messages)
    latest_conversation.append(format_message(message)) 
    # buscar hacer esto ASYNC (para no afectar rendimiento)
    write_message(dynamodb, DYNAMODB_TABLE,
                   serialize_message(message, primary_key, role='user', metadata=metadata))
    
    #2. Determine Stage
    chat_stage = get_chat_stage(latest_conversation)

    #3. Enrutar stage
    match chat_stage:
        case 1: 
            from app.services.stages import stage1_extract
            response = stage1_extract.handle(latest_conversation)
        case _:
            response= 'stage no identificado'
    
    #4. Guardar respuesta BOT
    write_message(dynamodb, DYNAMODB_TABLE,
                serialize_message(response, primary_key, role='assistant', metadata=metadata))

    #5. Retornar respuesta
    return response

    
    