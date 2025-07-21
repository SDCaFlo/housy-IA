from app.core.aws_clients import get_bedrock_client
from langchain_aws.chat_models.bedrock_converse import ChatBedrockConverse
from app.core.config import BEDROCK_MODEL_ID
from app.models.PropertyLead import PropertyLead
from langchain_core.runnables import RunnableLambda, RunnableBranch
from langchain_core.prompts import PromptTemplate
#doc: https://python.langchain.com/api_reference/aws/index.html
#doc: https://python.langchain.com/api_reference/aws/chat_models/langchain_aws.chat_models.bedrock_converse.ChatBedrockConverse.html#langchain_aws.chat_models.bedrock_converse.ChatBedrockConverse


BASE_PROMPT = "Simula ser un asesor inmobiliario que guía al usuario con preguntas "\
        "para entender qué tipo de propiedad desea el cliente llenando los datos REQUERIDOS."\
        " Sé breve pero cordial y amigable. (máx 50 palabras)." \
        "❗Actualmente los datos FALTANTES son: {datos_faltantes} <- Pregunta por estos ❗"\
        " Como contexto ten en cuenta los datos que podemos recolectar y su descripción:" \
        "{data_info}"

LEAD_PROMPT = """A partir del siguiente historial de mensajes de usuario, extrae únicamente los datos explícitamente mencionados.

            ❗No completes campos por inferencia.  
            ❗Si el dato no está mencionado literalmente o con sinónimos claros, déjalo como `None`.

            No asumas que busca alquiler solo porque menciona "departamento", ni que busca compra porque menciona "terreno". Solo responde con datos explícitos.

            Historial de mensajes:
            {input}
            """

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
    
    build_lead_prompt_chain = RunnableLambda(lambda vars: build_lead_prompt(conversation= vars['conversation']))
    get_lead_chain = RunnableLambda(lambda vars: get_lead_with_prompt(lead_prompt=vars['lead_prompt']))
    #lead_extraction_chain = RunnableLambda(lambda vars: get_lead(conversation = vars['conversation']))
    lead_verification_chain = RunnableLambda(lambda vars: has_minimium_data(lead=vars['lead']))
    get_missing_keys_chain =  RunnableLambda(lambda vars: get_missing_info(lead=vars['lead']))

    # Definicion de cadenas principales.
    pre_chain = (
        RunnableLambda(lambda vars: vars)
        .assign(lead_prompt = build_lead_prompt_chain)          # construimos el prompt_lead
        .assign(lead = get_lead_chain)                          # extramos lead
        .assign(lead_verification = lead_verification_chain)    # verificacion de campos requeridos
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
        .assign(missing_info = get_missing_keys_chain)
        .assign(final_prompt = build_prompt_chain)
        .assign(model_response = contact_llm_chain)
    )

    branch_chain = RunnableBranch(
        (lambda vars: vars["lead_verification"], true_chain),   # condición si True
        false_chain                                             # si False
    )

    # Cadena final
    full_chain = (pre_chain | branch_chain)

    # Invocacion de cadena
    result = full_chain.invoke(
        {'conversation': conversation,
         'base_prompt': BASE_PROMPT}
    )
   
    return result


def model_converse(prompt, conversation):
    """Conversation with langchain bedrock."""
    
    chat = get_langchain_bedrock_client()                        # client        
    messages =   message_with_prompt_build(prompt, conversation) # Message construction
    response = chat.invoke(messages)                             # invoke model
    return response.content


def get_lead(conversation):
    """Obtiene un lead formateado segun la clase definida en app.models.PropertyLead"""

    chat = get_langchain_bedrock_client(**LEAD_GENERATION_PARAMS)
    structured_llm = chat.with_structured_output(PropertyLead)
    prompt = build_lead_prompt(conversation)
    
    return structured_llm.invoke(prompt)

def get_lead_with_prompt(lead_prompt:str, include_raw:bool = False):
    """Obtiene un lead formateado segun la clase definida en app.models.PropertyLead
    Usa un prompt ya definido"""

    chat = get_langchain_bedrock_client(**LEAD_GENERATION_PARAMS)
    structured_llm = chat.with_structured_output(PropertyLead, include_raw=include_raw)
    
    return structured_llm.invoke(lead_prompt)


def has_minimium_data(lead: PropertyLead) -> bool:
    """Determina si se tiene la minima data para continuar con el siguiente stage"""
    return all([
        lead.ubicacion,
        lead.tipo_propiedad,
        lead.transaccion
    ])

def get_missing_info(lead: PropertyLead) -> str:
    """Nos brinda una str con los datos faltantes para poder realizar una búsqueda"""
    missing_info = []
    dict_lead = {
        "ubicacion" : lead.ubicacion,
        "propiedad" : lead.tipo_propiedad,
        "transaccion" : lead.transaccion
    }

    for key, value in dict_lead.items():
        if value == None:
            missing_info.append(key.upper())
    
    return ", ".join(missing_info) + "!."

def get_missing_info_2(lead: PropertyLead) -> str:
    """Nos brinda una str con los datos faltantes para poder realizar una búsqueda"""
    missing_info = []
    dict_lead = dict(lead)

    for key, value in dict_lead.items():
        if value == None:
            missing_info.append(key)
    
    return ", ".join(missing_info)



#### UTILS ####


def build_lead_prompt(conversation):
    """Construye un prompt para la generación de lead"""

    message_history = ""

    for message in conversation:
        if message['role']=='user':
            message_history += " " + message['content'][0]['text'] + '\n'

    return LEAD_PROMPT.format(input=message_history)



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
    data_context = build_data_context()
    final_prompt = base_prompt.format(
        datos_faltantes = missing_info,
        data_info = data_context
    )
    return final_prompt


def build_data_context() -> str:
    """Construimos el contexto de la data a partir de la clase PropertyLead"""
    data_context = ""
    for key,value in dict(PropertyLead.model_fields.items()).items():
        data_info = key +  ": " + value.description
        data_context += data_info + "\n"
    return data_context.strip("\n")


def get_langchain_bedrock_client(max_tokens: int = 250, temperature: float = 0.6, top_p: float =0.6):
    """Sets up langchain bedrock client"""
    client = get_bedrock_client()
    
    #client config
    chat = ChatBedrockConverse(
        client=client,
        model=BEDROCK_MODEL_ID,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p
        )
    return chat

