from app.core.aws_clients import get_langchain_bedrock_client
from langchain_core.runnables import RunnableLambda
from app.models.PropertyLead import PropertySearchParams
from app.core.config import ROUTER_MODEL_ID
from app.models.LLM_prompts import ROUTER_PROMPT
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

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


