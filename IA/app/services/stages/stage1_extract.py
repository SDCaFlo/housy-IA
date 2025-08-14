from app.core.aws_clients import get_langchain_bedrock_client
from app.core.config import BEDROCK_MODEL_ID
from app.models.PropertyLead import PropertyLead, PropertySearchParams
from langchain_core.runnables import RunnableLambda, RunnableBranch
from app.services.stages.stage_logic import summarize_conversation, Conversation
#doc: https://python.langchain.com/api_reference/aws/index.html
#doc: https://python.langchain.com/api_reference/aws/chat_models/langchain_aws.chat_models.bedrock_converse.ChatBedrockConverse.html#langchain_aws.chat_models.bedrock_converse.ChatBedrockConverse


BASE_PROMPT = "Simula ser un asesor inmobiliario que guía al usuario con PREGUNTAS "\
        "para entender qué tipo de propiedad desea el cliente."\
        " Sé breve pero cordial y amigable. (máx 50 palabras)." \
        "❗NO RECOMENDEMOS NADA, solo hagamos preguntas."\
        "❗Actualmente los datos FALTANTES son: {datos_faltantes} <- Pregunta por estos ❗"\
        " Como contexto ten en cuenta los datos que podemos recolectar y su descripción:" \
        "{data_info}"


LEAD_GENERATION_PARAMS = {"max_tokens": 250, "temperature": 0.7  , "top_p" : 0.7}


def handle(conversation):

    """Logica langchain del chatbot stage - 1
    Ejemplo de conversación:
    [{'role': 'user',
        'content': [{"text": "Hello"}]},
       {'role': 'assistant',
        'content': [{"text": "Hola, en que puedo ayudarte?"}]}, 
    ]
    """

    # Wrap de funciones en cadenas Langchain:
    build_prompt_chain = RunnableLambda(lambda vars: build_question_prompt(
        base_prompt=vars["base_prompt"],
        missing_info=vars["missing_info"]
    ))
    contact_llm_chain = RunnableLambda(lambda vars: model_converse(
        prompt=vars["final_prompt"],
        conversation=vars["conversation"]
    ))

    ## new lambdas and chain
    get_conversation_class = RunnableLambda(lambda vars: Conversation(message_history=vars['conversation']))
    get_lead = RunnableLambda(lambda vars: vars['conversation_class'].get_lead())
    lead_verification = RunnableLambda(lambda vars: vars['conversation_class'].verify_lead())
    get_missing_params = RunnableLambda(lambda vars: vars['conversation_class'].get_missing_params())

    new_chain = (
        RunnableLambda(lambda vars: vars)
        .assign(conversation_class = get_conversation_class)
        .assign(lead = get_lead)
        .assign(lead_verification = lead_verification)
    )

    true_chain = (
        RunnableLambda(lambda vars: {
            **vars,
            "next_stage" : True
        })
    )
    
    false_chain = (
         RunnableLambda(lambda vars: {
            **vars,
            "next_stage" : False
        })
        .assign(missing_info = get_missing_params)
        .assign(final_prompt = build_prompt_chain)
        .assign(model_response = contact_llm_chain)
    )

    branch_chain = RunnableBranch(
        (lambda vars: vars["lead_verification"], true_chain),   # condición si True
        false_chain                                             # si False
    )

    # Cadena final
    full_chain = (new_chain | branch_chain)

    # Invocacion de cadena
    result = full_chain.invoke(
        {'conversation': conversation,
         'base_prompt': BASE_PROMPT}
    )
   
    return result


def model_converse(prompt, conversation):
    """Conversation with langchain bedrock."""
    
    chat = get_langchain_bedrock_client(model_id=BEDROCK_MODEL_ID)                        # client        
    messages =   message_with_prompt_build(prompt, conversation) # Message construction
    response = chat.invoke(messages)                             # invoke model
    return response.content


#### UTILS ####


def message_history_build(conversation):
    """Da formato a una conversacion para ser pasada a conversation API de langchain_aws.bedrockConverse Api"""
    conversation_list = []
    for message in conversation:
        if message['role'] == 'assistant':
            conversation_list.append(('assistant', message['content'][0]['text']))
        else:
            conversation_list.append(('user', message['content'][0]['text']))
    return conversation_list


def message_with_prompt_build(prompt, conversation):
    """Construye un mensaje con prompt listo para pasar al método .invoke"""
    messages = [ ("system", prompt), ]
    try:
        message_history = message_history_build(conversation)
        messages.extend(message_history)
    except: 
        pass
    return messages


def build_question_prompt(base_prompt: str, missing_info: str):
    """Construye un prompt para preguntar la informacion faltante, considerando la informacion minima requerida"""
    data_context = PropertySearchParams.describe_class()
    final_prompt = base_prompt.format(
        datos_faltantes = missing_info,
        data_info = data_context
    )
    return final_prompt




