from app.models.PropertyLead import PropertySearchParams
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

def get_extract_chain():
    #1. Creamos el parser
    parser = PydanticOutputParser(pydantic_object=PropertySearchParams)

    #2. Prompt
    prompt = PromptTemplate(
        template=EXTRACT_PROMPT,
        input_variables=["input"],
        partial_variables={
            "format_instructions": parser.get_format_instructions(),
            "full_lead": PropertySearchParams.generate_example_lead_str(full=True),
            "empty_lead": PropertySearchParams.generate_example_lead_str(full=False)
            }
    )

    # 3. Definir el modelo
    model_id = NER_MODEL_ID
    logger.info(f'Extract chain: Model ID: {NER_MODEL_ID}')
    llm = get_langchain_bedrock_client(model_id=model_id, max_tokens=500, temperature=0, top_p=1)

    chain = (
        RunnablePassthrough.assign(extract_formatted_prompt=lambda x: prompt.invoke({"input": x["user_message"]})
        )
        | RunnablePassthrough.assign(
            extract_llm_raw_output=lambda x: llm.invoke(x["extract_formatted_prompt"])
        )
        | RunnablePassthrough.assign(
            extract_parsed_lead=lambda x: parser.invoke(x["extract_llm_raw_output"])
        )
        | RunnablePassthrough.assign(
            extract_merged_lead=lambda x: deepcopy(x["input_lead"]).merge_with(x["extract_parsed_lead"])
        )
    )

    return chain
