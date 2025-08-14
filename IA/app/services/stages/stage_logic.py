### Logic an utilities for all stages ###
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.models.PropertyLead import PropertyLead, PropertySearchParams
import json
from app.core.aws_clients import get_langchain_bedrock_client
from app.services.tools.geo_lookup import geocode_address as geocode_address
from app.core.config import SUMMARIZE_MODEL
from typing import List

LEAD_PROMPT =  rf"""
        Eres un asistente inteligente especializado en bienes raíces. Tu función es extraer datos sobre las necesidades de cliente.

        Dada una conversación, ejecuta los siguientes pasos:

        1. Resume las necesidades de cliente y arma un texto que explique con detalles lo que el cliente está buscando.
                - Se lo más conciso posible.
                - Si el cliente cambia de opinión con respecto a algo, usar la información más reciente.

        2. Identificar las entidades relevantes:
                - Hagamos una lista de posibles entidades relevantes: ubicación, tipo de propiedad(casa, departamento, etc), superficie, presupuesto, etc.
                - Si se mencionan aproximados (rangos no definidos), creemos un rango prudente. Ejm: 'Presupuesto de 2500 soles' -> precio mínimo:2000 y precio máximo:3000
        
        3. Realizar Named Entity Recognition (NER):
                - En base a las entidades identificadas, devuelve un diccionario categorizado por tipo.
                - Solo rellenar los campos identificados.
                - Para temas de presupuesto tener en cuenta lo siguiente:
                        - 'Presupuesto máximo de 2000 soles' → max_price: 2000
                        - 'Presupuesto mínimo de 1000 soles' → min_price: 1000
                        - Inexactos, ambiguos , asumir un rango: 'Presupuesto aproximado de 2000': → min_price:1500, max_price:2500
                - Ejemplo: {str(json.dumps(PropertySearchParams.get_sample_element())).replace('{', '{{').replace('}','}}')}

        ❗No completes campos por inferencia.
        📌 Si el cliente no brinda información válida, no inventemos y devolvamos un texto indicando que no se tiene mayores detalles.
"""

SUMMARIZE_PROMPT = """
Eres un asistente especializado en bienes raíces. Tu tarea es resumir las necesidades actuales del cliente basándote en el historial completo de la conversación.

✅ Si el cliente cambió de opinión o corrigió algún dato durante la conversación, incluye **solo la versión más reciente de cada necesidad** (por ejemplo: ubicación, tipo de propiedad, intención de compra o alquiler, etc.).
📌 No menciones los cambios previos ni el historial del diálogo. Solo entrega el resultado final como una **oración breve y clara en lenguaje natural**.
❗No completes campos por inferencia.
📌 Si el cliente no brinda información válida, no inventemos y devolvamos un texto indicando que no se tiene mayores detalles.

Responde únicamente con ese resumen, sin encabezados, explicaciones ni listas.
"""

class Conversation:
    """Clase para manejar la conversación y generación de LEADs con cliente.
    Utilidades:
        - Guarda la conversación
        - Analiza la conversación y retorna un LEAD.
        - Verifica si el LEAD es válido.
        - Verifica parámetros faltantes en el LEAD.
    """

    mandatory_params = ['property_types', 'operation_type', 'location']

    def __init__(self, message_history=[]):
        self.conversation_unformatted = message_history
        self.conversation = self.format_message_history(message_history)
        self.lead = None

    def format_message_history(self, message_history: list):
        """Da formato a una conversación proveniente en el siguiente formato: 
            input = [
                {'role': 'user', 'content': [{"text": "Hello"}]},
                {'role': 'assistant','content': [{"text": "Hola, en que puedo ayudarte?"}]}, 
            ]
        
        """
        formatted_conversation = []
        for message in message_history:
            match message['role']:
                case 'user':
                    formatted_conversation.append(HumanMessage(content=message['content'][0]['text']))
                case 'assistant':
                    formatted_conversation.append(AIMessage(content=message['content'][0]['text']))
                case _:
                    pass
        return formatted_conversation
    

    def get_lead(self, model_id = "amazon.nova-lite-v1:0", model_params = {'max_tokens': 250, 'temperature' : 0.0, 'top_p' : 1}) -> PropertySearchParams:
        """Obtiene un lead en base a la conversación"""
        llm = get_langchain_bedrock_client(model_id, **model_params)
        structured_llm = llm.with_structured_output(schema=PropertySearchParams)
        
        system_prompt = SystemMessage(content=LEAD_PROMPT)

        self.lead = structured_llm.invoke(
            input=[
                system_prompt,
                *self.conversation
            ]
        )

        return self.lead
    
    def verify_lead(self) -> bool:
        """Verifica si el LEAD tiene la información mínima requerida"""
        dict_lead = dict(json.loads(json.dumps(dict(self.lead))))
        
        for param in self.mandatory_params:
            if dict_lead.get(param) in ([], None):
                return False
            
        return True
    
    def get_missing_params(self) -> List[str]:
        """Retorna una lista con los valores faltantes para completar el lead"""
        missing_params = []

        dict_lead = dict(json.loads(json.dumps(dict(self.lead))))

        for param in self.mandatory_params:
            if dict_lead.get(param) in ([], None):
                missing_params.append(param)
            
        return missing_params
        



def summarize_conversation(conversation)->str:
    """Llamamos al modelo de BEDROCK para resumir"""
    conversation_chat_history = ' '.join([ message['content'][0]['text']for message in conversation ])

    chat_summary_prompt = [
        SystemMessage(content=SUMMARIZE_PROMPT),
        HumanMessage(content=conversation_chat_history)
    ]

    chat = get_langchain_bedrock_client(SUMMARIZE_MODEL)
    response = chat.invoke(chat_summary_prompt)

    return response.content

def get_chat_stage_metadata(latest_messages):
    for msg in reversed(latest_messages):
        try:
            metadata = msg.get("metadata", {})
            if isinstance(metadata, dict) and "stage" in metadata:
                return metadata["stage"]
        except Exception:
            continue
    return "extract"


def get_model_message(stage, response):
    model_message = ""
    try:
        match stage:
            case "extract":
                model_message = response["model_response"]
            case "recommend":
                model_message = str(response)
            case _:
                pass
    except Exception as e:
        model_message = f"error matching message: {e}"
    
    return model_message

