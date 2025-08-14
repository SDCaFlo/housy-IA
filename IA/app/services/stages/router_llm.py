from app.core.aws_clients import get_langchain_bedrock_client
from langchain_core.runnables import RunnableLambda, RunnableBranch
from app.models.PropertyLead import PropertySearchParams
from app.core.config import ROUTER_MODEL_ID
from app.models.LLM_prompts import ROUTER_PROMPT

class LlmRouter():
    def __init__(self):
        self.llm = get_langchain_bedrock_client(
            model_id=ROUTER_MODEL_ID,
        )

    def config(self,  new_message, current_state, entities=PropertySearchParams().model_dump_json(), message_history=[]):
        self.new_message = new_message
        self.current_state = current_state
        self.entities = entities
        self.message_history = message_history

    def route(self):
        chain = RunnableLambda(lambda vars:
                    ROUTER_PROMPT.format(
                        message_history = self.message_history,
                        new_message = self.new_message,
                        current_state = self.current_state,
                        entities = self.entities
                        )
                    ) | self.llm
        return chain
        


