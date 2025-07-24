from app.models.ChatMessage import ChatHistoryElement, ChatMessage
from app.core.config import DYNAMODB_TABLE
from boto3.dynamodb.types import TypeDeserializer
from app.services.dynamodb_queries import get_latests_messages, get_metadata,deserialize_item
from app.services.dynamodb_queries import message_wrapper_flex, serialize_item, write_message


def proccess_chat_turn(user_id: str, conv_id:str, message:str, metadata:dict = {}, verbose:bool = False):
    """Logica por stages para el procesamiento de chats"""

    primary_key = "USER#"+user_id+"#CONV#"+conv_id

    #1. Get Chat History
    # recuperamos historial, damos formato al nuevo mensaje y juntamos todo en una sola variable.

    conversation_length = get_conversation_length(primary_key)
    latest_messages = get_latests_messages(primary_key, limit=conversation_length)
    latest_conversation = convert_to_conversation(latest_messages)
    latest_conversation.append(format_message(message))

    
    #2. Determine Stage
    try:
        chat_stage = get_metadata(latest_messages)[0]['stage'] # obtiene el ultimo stage del historial de conversacion
    except:
        chat_stage = "extract"      # si no es posible, asumir extract stage

    #3. Route stage
    for i in range(5): #loop protect (5 times)
        print("loop count: ", i)
        match chat_stage:
            case "extract": 

                from app.services.stages.stage1_extract import handle as stage1_handler

                response = stage1_handler(latest_conversation)
    
                lead = response["lead"]             # recuperamos el lead

                if response["next_stage"] == True:
                    from app.services.stages.stage2_recommend import handler as stage2_handler
                    chat_stage = "recommend"    # cambiamos el chat_stage si amerita.
                    response = stage2_handler(lead) # ejecutamos el siguiente stage directamente y asociamos su respuesta
                
                break
            case "recommend":
                from app.services.stages.stage3_intent import handler as stage3_handler
                # Analizamos intent y determinamos siguiente stage
                response = stage3_handler(user_message=message)
                chat_stage = response.get('next_stage')
                
                if chat_stage == 'extract':
                    # Regresamos al stage 1, considerando una nueva conversación.
                    conversation_length = 0
                    latest_conversation = [latest_conversation[-1]]
            
            case "refine_search":
                # de momento solo redirigimos hacia stage 1.
                #response = "pending from refine_logic"
                #lead = None
                chat_stage = 'extract'

    
    #metadata modification:
    metadata["stage"] = chat_stage
    metadata["lead"] = lead
    metadata["conversation_length"] = conversation_length + 2.0
    
    #4. Guardar Mensajes
    #saving user message:
    save_user_message(primary_key, message, metadata)
    save_response_message(primary_key, response, metadata, chat_stage)

    #5. Retornar respuesta
    return chat_stage, response



# Other utilities

def format_message(message: str, role: str="user"):
    """Formatea el mensaje del cliente para que devuelva 
    estructura de mensaje para bedrock"""
    return {'role': role, 'content': [{'text': message}]}


def save_user_message(primary_key, message, metadata):
    """Code for formatting user message and saving into dynamoDB"""

    try:
        user_data_dict = {
            "PK" : primary_key,
            "role" : "user",
            "content_type": "text",
            "content": {
                "text" : message
            },
            "metadata": metadata
        }
        user_message_dict = message_wrapper_flex(user_data_dict)
        formatted_message = ChatMessage(**user_message_dict)
        serialized_user_message = serialize_item(formatted_message)
        return write_message(DYNAMODB_TABLE, serialized_user_message)
    except Exception as e:
        print(f"Error saving user message: {e}")
        return None
    
def save_response_message(primary_key:str, response, metadata:dict, stage:str):
    """Code for formatting response and saving into dynamoDB"""
    try:
        match stage:
            case "extract":
                data_dict = {
                    "PK" : primary_key,
                    "role" : "assistant",
                    "content_type": "text",
                    "content": {
                        "text" : response.get('model_response')
                    },
                    "metadata": metadata
                }
            case "recommend":
                data_dict = {
                    "PK" : primary_key,
                    "role" : "assistant",
                    "content_type": "property_list",
                    "content": {
                        "properties" : response
                    },
                    "metadata": metadata
                }
            case _:
                data_dict = {
                    "PK" : primary_key,
                    "role" : "assistant",
                    "content_type": "text",
                    "content": {
                        "text" : "error saving response message"
                    },
                    "metadata": metadata
                }
        message_dict = message_wrapper_flex(data_dict)
        formatted_message = ChatMessage(**message_dict)
        ser_item = serialize_item(formatted_message)
        return write_message(DYNAMODB_TABLE, ser_item)
    except Exception as e:
        print(f"Error saving response message: {e}")
        return None


def convert_to_conversation(latest_messages):
    """Convierte los mensajes en una conversación bedrock"""
    messages = []
    for serialized_item in latest_messages.get("Items"):
        item = deserialize_item(serialized_item)

        match item.get('content_type'):
            case 'text':
                content = item.get('content').get('text')
            case 'property_list':
                content = '**Te recomendamos las siguientes propiedades** : (Lista de propiedades)'
            case _:
                content = 'Not defined content type'

        message_entry = {
            'role': item.get('role'),
            'content': [{'text': content}]
        }

        messages.append(message_entry)
    return messages



def get_conversation_length(primary_key: str) -> int:
    """Permite recuperar la cantidad de mensajes dentro del contexto actual"""

    try:
        last_message = get_latests_messages(primary_key, limit=1)
        conversation_length = int(last_message['Items'][0]['metadata']['M']['conversation_length']['N'])
    except Exception as e:
        conversation_length = 0
        print('Stage_1:message_recovery: No conversation history found')

    return conversation_length