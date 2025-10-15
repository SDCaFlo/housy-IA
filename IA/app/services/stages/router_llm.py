from app.core.aws_clients import get_langchain_bedrock_client
from app.models.PropertyLead import PropertySearchParams
from app.models.ChatState import InputRouter, route_descriptions
from app.core.config import ROUTER_MODEL_ID
from app.models.LLM_prompts import ROUTER_PROMPT, ROUTER_PROMPT_v5
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.output_parsers import BaseOutputParser
import logging


class RobustEnumParser(BaseOutputParser[InputRouter]):
    """Parser que extrae el enum incluso si hay texto adicional"""
    
    def parse(self, text: str) -> InputRouter:
        # Limpia el texto
        text_lower = text.strip().lower()
        
        # Busca cada posible valor
        for route in InputRouter:
            if route.value in text_lower:
                # Verifica que sea una palabra completa, no parte de otra
                if f" {route.value} " in f" {text_lower} " or \
                   text_lower.startswith(route.value) or \
                   text_lower.endswith(route.value):
                    return route
        
        # Default
        logging.warning(f"No se encontró ruta válida en: {text}. Usando extract por defecto.")
        return InputRouter.extract


class LlmRouter:
    def __init__(self):
        self.llm = get_langchain_bedrock_client(
            model_id=ROUTER_MODEL_ID,
        )

    def config(
        self,
        new_message: str,
        current_state: dict,
        entities: PropertySearchParams = PropertySearchParams().model_dump_json(),
        message_history: list = [],
    ):
        self.new_message = new_message
        self.current_state = current_state
        self.entities = entities
        self.message_history = message_history

        self.system_prompt = str(
            ROUTER_PROMPT.format(
                current_state=str(self.current_state)
                .replace("{", "{{")
                .replace("}", "}}"),
                entities=str(self.entities).replace("{", "{{").replace("}", "}}"),
            )
        )

        # Definir el prompt con placeholder para historial
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

    def get_chain(self):
        chain = self.prompt | self.llm
        return chain

    def route(self):
        chain = self.get_chain()
        response = chain.invoke(
            {"history": self.message_history, "input": self.new_message}
        )
        return response.content

    def get_chain_parameters(self):
        return {"history": self.message_history, "input": self.new_message}

def get_route_chain():
    parser = RobustEnumParser()
    
    formatted_descriptions = "\n\n".join(
        f"{route.value}:\n{desc.strip()}" 
        for route, desc in route_descriptions.items()
    )

    prompt = PromptTemplate(
        template=ROUTER_PROMPT_v5,
        input_variables=["message_context"],
        partial_variables={
            "route_descriptions": formatted_descriptions
        },
    )

    llm = get_langchain_bedrock_client(
        model_id=ROUTER_MODEL_ID, temperature=0.0, max_tokens=50
    )

    return prompt | llm | parser
