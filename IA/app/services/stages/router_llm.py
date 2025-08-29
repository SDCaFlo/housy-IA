from app.core.aws_clients import get_langchain_bedrock_client
from app.models.PropertyLead import PropertySearchParams
from app.models.ChatState import InputRouter
from app.core.config import ROUTER_MODEL_ID
from app.models.LLM_prompts import ROUTER_PROMPT, ROUTER_PROMPT_v3
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain.output_parsers import EnumOutputParser




class LlmRouter():
    def __init__(self):
        self.llm = get_langchain_bedrock_client(
            model_id=ROUTER_MODEL_ID,
        )

    def config(self,  new_message: str,
               current_state:dict,
               entities: PropertySearchParams=PropertySearchParams().model_dump_json(), 
               message_history: list= []):
        self.new_message = new_message
        self.current_state = current_state
        self.entities = entities
        self.message_history = message_history

        self.system_prompt = str(
            ROUTER_PROMPT.format(
                current_state = str(self.current_state).replace("{", "{{").replace("}","}}"),
                entities = str(self.entities).replace("{", "{{").replace("}","}}")
                )
                )
        
        #Definir el prompt con placeholder para historial
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")    
        ])
    
    def get_chain(self):
        chain = self.prompt | self.llm
        return chain
        
    def route(self):
        chain = self.get_chain()
        response = chain.invoke(
            {"history": self.message_history,
             "input": self.new_message}
        )
        return response.content
    
    def get_chain_parameters(self):
        return {"history": self.message_history, "input": self.new_message}
    
def get_route_chain():

    llm = get_langchain_bedrock_client(model_id=ROUTER_MODEL_ID, temperature=0.1, max_tokens=5)

    prompt = ChatPromptTemplate.from_messages([
            ("system", ROUTER_PROMPT), # inputs: input_states, entities
            ("human", "{input}")    
        ])
    
    return prompt | llm

def get_route_chain_v2():

    parser = EnumOutputParser(enum=InputRouter)
    format_instructions = parser.get_format_instructions()

    prompt = PromptTemplate(
        template= ROUTER_PROMPT_v3,
        input_variables=[
            #"input_state", "entities", 
            "user_message"],
        partial_variables={
            "route_options": ', '.join([r.value for r in InputRouter]),
            "format_instructions": format_instructions
        }
    )

    llm = get_langchain_bedrock_client(model_id=ROUTER_MODEL_ID, temperature=0.1, max_tokens=20)

    return prompt | llm | parser