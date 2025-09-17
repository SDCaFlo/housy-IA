import logging
from app.core.aws_clients import get_langchain_bedrock_client
from app.models.LLM_prompts import QUERY_PROMPT
from app.core.config import QUERY_USER_MODEL_ID

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_query_user_chain():
    """Contact a LLM y realiza preguntas al usuario."""

    # 1. Definimos el prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", QUERY_PROMPT),
            MessagesPlaceholder(variable_name="message_history"),
            ("human", "{input}"),
        ]
    )

    # 2. Definimos el modelo
    model_id = QUERY_USER_MODEL_ID
    logger.info(f"Query user chain: Model ID: {QUERY_USER_MODEL_ID}")
    llm = get_langchain_bedrock_client(model_id=model_id)

    # 3. Creamos cadena y retornamos la misma
    chain = prompt | llm

    return chain
