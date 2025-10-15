from app.core.aws_clients import get_langchain_embed_client, get_langchain_bedrock_client
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.core.config import AURORA_DB_USER, AURORA_DB_PASSWORD, AURORA_DB_URL, FAQ_MODEL_ID
from app.models.LLM_prompts import FAQ_PROMPT_V1
from app.models.ChatState import MyState
from langchain_postgres import PGVector
import logging



def faq_retrieve_node(state: MyState):
    """Codigo para creación del nodo retrieve"""
    logging.info("faq_retrieve_node: Entered faq_retrieve node")
    retriever = get_vector_store().as_retriever(search_kwargs={"k":3})
    docs = retriever.invoke(state.user_message)
    state.faq_retrieve_result = [doc.page_content for doc in docs]
    state.current_state_flow.append("faq_retrieve")
    logging.info("faq_retrieve_node: Exiting faq_retrieve node")
    return state


def faq_llm_node(state: MyState):
    """Codigo para creación del nodo LLM que absorve el retrieve"""
    logging.info("faq_llm_node: Entered faq_llm node")
    chain = get_faq_llm_chain()
    result = chain.invoke({
        'context': '\n\n'.join(state.faq_retrieve_result),
        'input': state.user_message,
        'message_history': state.message_history
    })
    state.faq_llm_result["llm_raw_output"] = result
    state.faq_llm_result["faq_llm_output"] = result.model_dump().get(
        "content", "error"
    )
    state.current_state_flow.append('faq_llm')
    logging.info("faq_llm_node: Exiting faq_llm node")
    return state        


def get_vector_store():
    """Gets a langchain pg vector store object"""
    db_name = "documents"
    collection_name = "faq_embeddings"

    CONNECTION_STRING = rf"postgresql+psycopg://{AURORA_DB_USER}:{AURORA_DB_PASSWORD}@{AURORA_DB_URL}:5432/{db_name}"
    print("Connection string: ",CONNECTION_STRING)

    embed_client = get_langchain_embed_client()

    vector_store = PGVector(
        connection=CONNECTION_STRING,
        embeddings=embed_client,
        collection_name=collection_name
    )

    return vector_store


def get_faq_llm_chain():
    """Creates an LLM chain to contact with the LLM."""
    #1. Creamos el prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", FAQ_PROMPT_V1),                              # variable: 'context'
            MessagesPlaceholder(variable_name="message_history"),   # variable: 'message_history'
            ("human", "{input}")                               # variable: 'input'
        ]
    )

    #2. Definimos el LLM
    llm = get_langchain_bedrock_client(model_id=FAQ_MODEL_ID)
    
    return prompt | llm
