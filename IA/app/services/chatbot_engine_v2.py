from app.models.ChatHistory import ChatHistory
from app.services.stages.router_llm import LlmRouter

def proccess_chat_turn(user_id: str, conv_id:str, message:str, metadata:dict = {}, verbose:bool = False):
    """Logica por stages para el procesamiento de chats"""

    # 1. Recuperar los mensajes históricos.
    # Necesitamos los siguientes datos para nuestro planner: 
    # previous_state + message_history + entities .

    chat_history = ChatHistory(user_id, conv_id)
    chat_history.get_messages(chat_history.context_length) #contacts dynamodb and retrieves messages.
    current_state, state_count = chat_history.retrieve_current_stage()
    current_lead = chat_history.retrieve_current_lead()
    formatted_history = chat_history.get_langchain_history()

    # contact router LLM.
    router = LlmRouter()
    router.config(message, 
                  {'current_state' : current_state,'state_count': state_count}, 
                  current_lead,
                  formatted_history
                  )
    ## pendiente crear funcion para dar un formato bonito a los mensajes







