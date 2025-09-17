from app.models.PropertyLead import PropertySearchParams
from rapidfuzz import process
from app.core.aws_clients import get_langchain_bedrock_client
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.models.LLM_prompts import EXTRACT_PROMPT
from app.core.config import NER_MODEL_ID
import logging
from copy import deepcopy


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


OPERATION_SYNONYMS = {
    "alquiler": ["alquiler", "arriendo", "arrendar", "rentar", "rent"],
    "venta": ["venta", "vender", "compra", "comprar", "buy"],
}

ALL_TERMS = [
    (syn, canonical) for canonical, syns in OPERATION_SYNONYMS.items() for syn in syns
]


def get_extract_chain():
    # 1. Creamos el parser
    parser = PydanticOutputParser(pydantic_object=PropertySearchParams)

    # 2. Prompt
    prompt = PromptTemplate(
        template=EXTRACT_PROMPT,
        input_variables=["input"],
        partial_variables={
            "format_instructions": parser.get_format_instructions(),
            "full_lead": PropertySearchParams.generate_example_lead_str(full=True),
            "empty_lead": PropertySearchParams.generate_example_lead_str(full=False),
        },
    )

    # 3. Definir el modelo
    model_id = NER_MODEL_ID
    logger.info(f"Extract chain: Model ID: {NER_MODEL_ID}")
    llm = get_langchain_bedrock_client(
        model_id=model_id, max_tokens=500, temperature=0, top_p=1
    )

    chain = (
        RunnablePassthrough.assign(
            normalized_message=lambda x: replace_operations_in_text(x["user_message"])
        )
        | RunnablePassthrough.assign(
            extract_formatted_prompt=lambda x: prompt.invoke(
                {"input": x["normalized_message"]}
            )
        )
        | RunnablePassthrough.assign(
            extract_llm_raw_output=lambda x: llm.invoke(x["extract_formatted_prompt"])
        )
        | RunnablePassthrough.assign(
            extract_parsed_lead=lambda x: parser.invoke(x["extract_llm_raw_output"])
        )
        | RunnablePassthrough.assign(
            extract_merged_lead=lambda x: deepcopy(x["input_lead"]).merge_with(
                x["extract_parsed_lead"]
            )
        )
    )

    return chain


def normalize_input_message(text: str) -> str:
    if not text:
        return None

    # Elegimos la mejor coincidencia de la lista
    match, score, _ = process.extractOne(
        query=text.lower(),
        choices=[term for term, _ in ALL_TERMS],
        score_cutoff=70,  # umbral de similitud (0-100)
    )

    if match:
        # recuperamos la forma canónica ("alquiler" o "venta")
        for term, canonical in ALL_TERMS:
            if term == match:
                return canonical
    return None


def replace_operations_in_text(text: str) -> str:
    words = text.split()
    normalized_words = []
    for w in words:
        match = process.extractOne(
            query=w.lower(), choices=[term for term, _ in ALL_TERMS], score_cutoff=80
        )
        if match:
            matched_term = match[0]
            canonical = next(c for t, c in ALL_TERMS if t == matched_term)
            normalized_words.append(canonical)
        else:
            normalized_words.append(w)
    return " ".join(normalized_words)
