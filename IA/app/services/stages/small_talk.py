from app.core.aws_clients import get_langchain_bedrock_client
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.models.LLM_prompts import SMALL_TALK_PROMPT_v1
from app.core.config import SMALL_TALK_MODEL_ID
import logging

def get_small_talk_chain():

    #1. Definimos el prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SMALL_TALK_PROMPT_v1),
            MessagesPlaceholder(variable_name="message_history"),
            ("human", "{input}"),
        ]
    )
    
    # 2. Definimos el modelo
    model_id = SMALL_TALK_MODEL_ID
    logging.info(f"small talk user chain: Model ID: {SMALL_TALK_MODEL_ID}")
    try:
        llm = get_langchain_bedrock_client(model_id=model_id)
    except Exception as e:
        print(e)
        logging.info(e)

    # 3. Creamos cadena y retornamos la misma
    chain = prompt | llm

    return chain