# IA/app/services/llm/langchain_bedrock.py

from app.services.llm_contact import call_model

class LangChainBedrockLLM:
    def __init__(self, system_prompt=None):
        """
        system_prompt: lista de mensajes tipo
          [{"role": "system", "content": "..."}]
        """
        self.system_prompt = system_prompt or []

    def generate(self, messages):
        """
        messages: lista de {"role": "user"|"assistant", "content": str}
        Devuelve el texto generado por el modelo.
        """
        # Llama a call_model con el formato adecuado
        return call_model(messages, self.system_prompt)
