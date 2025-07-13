# IA/app/agents/extract_city_chain.py

from app.services.llm_contact import call_model

def extract_city_chain():
    system_msgs = [{
        "text": (
            "Eres un asistente que extrae la ciudad mencionada en el mensaje del usuario. "
            "Devuelve solo el nombre de la ciudad."
        )
    }]

    def run(messages):
        user_msg = messages[-1]["content"]
        msgs = [{"role": "user", "content": user_msg}]
        return call_model(msgs, system_msgs).strip().lower()

    return run
