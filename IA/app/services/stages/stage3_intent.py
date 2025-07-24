from app.core.aws_clients import get_langchain_bedrock_client
from app.core.config import INTENT_DETECTION_MODEL
from langchain_core.runnables import RunnableLambda, RunnableBranch
from app.services.chatbot_engine import convert_to_conversation
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

INTENT_DETECTION_PROMPT = """ Eres parte de un sistema de búsqueda de propiedades inmobiliarias. 
    Tu tarea es detectar la intención del usuario y clasificarla dentro de las siguientes opciones:
    Debes responder con una sola palabra entre las siguientes opciones:
    - new_search: si el cliente quiere realizar una nueva búsqueda.
    - refine_search: si el cliente desea ajustar o agregar más datos a su búsqueda ya realizada.
"""

INTENT_DETECTION_PARAMS = {"max_tokens": 250, 
                          "temperature": 0.1  , 
                          "top_p" : 0.1}


def handler(user_message):
    """Handler stage 3"""

    intent_detect_chain = RunnableLambda(lambda vars: intent_detect(message=vars['user_message']).content)
    
    pre_chain = (
        RunnableLambda(lambda vars: vars)
        .assign(intent = intent_detect_chain)
    )

    new_search_chain = (
        RunnableLambda(lambda vars: {
            **vars,
            "next_stage" : 'extract'
        })
    )

    refine_search_chain = (
        RunnableLambda(lambda vars: {
            **vars,
            "next_stage" : 'refine_search'
        })
    )

    error_chain = (
        RunnableLambda(lambda vars: {
            **vars,
            "next_stage" : 'error_defining_intent'
        })
    )

    branch_chain = RunnableBranch(
        (lambda vars: vars['intent'] == 'new_search', new_search_chain),
        (lambda vars: vars['intent'] == 'refine_search', refine_search_chain),
        error_chain
    )

    full_chain = (pre_chain | branch_chain)

    result = full_chain.invoke(
        {'user_message' : user_message}
    )

    return result   



def intent_detect(message):
    """Lógica para el stage 3"""

    # generamos el intent detect en base al mensaje de usuario.
    message_input =  [{"role": "user", "content": message},]


    chat = get_langchain_bedrock_client(INTENT_DETECTION_MODEL, **INTENT_DETECTION_PARAMS)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", INTENT_DETECTION_PROMPT),
            ("user", "No me convencen los resultados."),
            ("assistant", "refine_search"),
            ("user", "Mejor que tenga tres habitaciones"),
            ("assistant", "refine_search"),
            ("user", "Quiero realizar otra búsqueda"),
            ("assistant", "new_search"),
            ("user", "Quiero explorar otra zona"),
            ("assistant", "new_search"),
            MessagesPlaceholder("message")
        ]
    )

    chain = prompt | chat

    response  = chain.invoke(
        {"message": message_input}
    )

    return response








