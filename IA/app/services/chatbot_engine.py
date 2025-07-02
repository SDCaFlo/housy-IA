
from typing import List, Dict
from app.models.ChatMessage import ChatMessage

#agregar busqueda de inmuebles
from app.services.embeddings.search_opensearch import search_similar_properties
from app.utils.intention_detection import tiene_intencion_busqueda  


# funciones como
# get_response
# get_context
# create_response
# user_chat

def format_message(message: str, role: str="user"):
    """Formatea el mensaje del cliente para que devuelva 
    estructura de mensaje para bedrock"""
    return {'role': role, 'content': [{'text': message}]}

def format_conversation(conversation_history):
    """Formats the output for chat history recovery"""
    formatted_history = []
    for item in conversation_history['Items'][::-1]:
        text = item['message']['S']
        role = item['role']['S']
        formatted_history.append({'role': role, 'message': text})
    return formatted_history

def get_chat_stage(conversation):
    pass # pending logic for stage definition
    return 1

def proccess_chat_turn(user_id: str, conv_id:str, message:str):
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
    #modificada por si en el futuro se usan roles
    latest_conversation.append(format_message(message, role="user"))
    # buscar hacer esto ASYNC (para no afectar rendimiento)
    write_message(dynamodb, "ChatMessages",
                   serialize_message(message, primary_key, role='user'))
    
     # 🔍 INTEGRACIÓN NUEVA: ¿Es una búsqueda inmobiliaria?
    if tiene_intencion_busqueda(message):
        resultados = search_similar_properties(message, k=3)
        if resultados:
            resultados_ordenados = sorted(resultados, key=lambda x: x['score'], reverse=True)
            texto_recomendacion = "🏡 Estas propiedades podrían interesarte:\n\n"
            for i, r in enumerate(resultados_ordenados, 1):
                texto_recomendacion += (
                    f"🏠 Propiedad recomendada #{i} (ID: {r['id']}, Score: {r['score']:.4f}):\n"
                    f"{r['text']}\n\n"
                )
            response = texto_recomendacion
        else:
            response = "No encontramos propiedades que coincidan. ¿Querés intentar con otra búsqueda?"
        
        # Guardar respuesta del BOT
        write_message(dynamodb, "ChatMessages",
                      serialize_message(response, primary_key, role='assistant'))
        
        return response  # Salimos aquí sin pasar por los stages

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
    write_message(dynamodb, "ChatMessages",
                serialize_message(response, primary_key, role='assistant'))

    #5. Retornar respuesta
    return response

    