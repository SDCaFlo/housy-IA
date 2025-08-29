from app.models.ChatHistory import ChatHistory
from app.services.stages.router_llm import get_route_chain
from app.services.stages.extract_chain import get_extract_chain
from langchain_core.runnables import RunnablePassthrough, RunnableBranch
import logging 

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def proccess_chat_turn(user_id: str, conv_id:str, user_message:str, metadata:dict = {}, verbose:bool = False):
    """Logica por stages para el procesamiento de chats"""

    # 1. Recuperar los mensajes históricos.
    # Necesitamos los siguientes datos para nuestro planner: 
    # previous_state + message_history + entities .

    chat_history = ChatHistory(user_id, conv_id)
    chat_history.get_messages(chat_history.context_length) #contacts dynamodb and retrieves messages.
    state  = dict(zip(['input_state', 'state_count'], chat_history.retrieve_current_stage()))
    input_lead = chat_history.retrieve_current_lead()
    formatted_history = chat_history.get_langchain_history()

    # contact router LLM.
    route_chain = get_route_chain()
    extract_chain = get_extract_chain()


    chain_estructurada = (
        {
            "input_state": lambda x: x["input_state"],
            "message_history": lambda x: x["message_history"],
            "user_message": lambda x: x["user_message"],
            "input_lead": lambda x: x["input_lead"]
        }
        #paso 1: rutear
        | RunnablePassthrough.assign(
            router_raw_response=lambda x: route_chain.invoke({
                "input": x["user_message"],
                "input_state": x["input_state"],
                "entities": str(x["input_lead"].model_dump()).replace("{", "{{").replace("}","}}"),
                "message_history": x["message_history"]
            })
        )
        | RunnablePassthrough.assign(
            router_route = lambda x: x['router_raw_response'].model_dump().get('content', 'error')
        )
        #paso 2: decision
        | RunnableBranch(
            (
                #extract chain
                lambda x: x["router_route"] == "extract",
                lambda x: {**x, **extract_chain.invoke(x)}
            ),
            # Default Chain
            RunnablePassthrough.assign(
                default_response=lambda x: f"Route '{x['route']}' not implemented yet"
            )
        )
    )

    response = chain_estructurada.invoke(
        {
            'input_state': str(state).replace("{", "{{").replace("}","}}"),
            'message_history': formatted_history,
            'user_message': user_message,
            'input_lead': input_lead
        }
    )

    return response


    
    
    
    







