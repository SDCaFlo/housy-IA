from app.models.ChatMessage import ChatHistoryElement
from app.core.config import DYNAMODB_TABLE
from boto3.dynamodb.types import TypeDeserializer


def proccess_chat_turn(user_id: str, conv_id:str, message:str, metadata:dict = {}, verbose:bool = False):
    """Logica por stages para el procesamiento de chats"""

    from app.core.aws_clients import get_dynamodb_client
    from app.services.dynamodb_queries import get_latests_messages, response_to_conversation, serialize_message, write_message, get_metadata
    from app.services.stages.stage_logic import get_model_message

    primary_key = "USER#"+user_id+"#CONV#"+conv_id

    #1. Get Chat History
    ''' - recuperamos contexto
        - anexamos nuevo mensaje
        - guardamos nuevo mensaje  '''
    dynamodb = get_dynamodb_client() # creacion sesion

        # recuperamos historial, damos formato al nuevo mensaje y juntamos todo en una sola variable.
    latest_messages = get_latests_messages(dynamodb, primary_key, limit=10)
    latest_conversation = response_to_conversation(latest_messages) 
    latest_conversation.append(format_message(message))

    
    #2. Determine Stage
    try:
        chat_stage = get_metadata(latest_messages)[-1]['stage'] # obtiene el ultimo stage del historial de conversacion
    except:
        chat_stage = "extract"      # si no es posible, asumir extract stage

    #3. Route stage
    match chat_stage:
        case "extract": 
            from app.services.stages.stage1_extract import handle as stage1_handler

            response = stage1_handler(latest_conversation)
 
            lead = response["lead"]             # recuperamos el lead

            if response["next_stage"] == True:
                from app.services.stages.stage2_recommend import handler as stage2_handler
                chat_stage = "recommend"        # cambiamos el chat_stage si amerita.
                response = stage2_handler(lead) # ejecutamos el siguiente stage directamente y asociamos su respuesta
            
        case "recommend":
            from app.services.stages.stage2_recommend import handler as stage2_handler
            lead = {
                "ubicacion": "Lima, Perú, San Isidro",
                "tipo_propiedad": "departamento",
                "transaccion": "alquiler",
                "presupuesto": None,
                "numero_dormitorios": 2,
                "numero_banos": 2,
                "metraje_minimo": None,
                "amenidades": ["gimnasio"],
                "cercania": None,
                "pet_friendly": True
            }
            response = stage2_handler(lead)
    
    #metadata modification:
    metadata["stage"] = chat_stage
    metadata["lead"] = lead
    
    #4. Guardar Mensajes
        # ( pendiente agregar chat_stage al guardar mensaje )
    model_message = get_model_message(chat_stage, response)
    try:
        write_message(dynamodb, DYNAMODB_TABLE,
            serialize_message(message, primary_key, role='user', metadata=metadata)) 
        write_message(dynamodb, DYNAMODB_TABLE,
                    serialize_message(model_message, primary_key, role='assistant', metadata=metadata))
    except Exception as e:
        print("error found: ")
        print(e)
        pass

    #5. Retornar respuesta
    return chat_stage, response



# Other utilities

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




    
    