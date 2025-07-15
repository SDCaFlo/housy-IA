# IA/test_chatbot.py
from app.graph.real_estate_chat import run_chatbot_flow

for msg in [
    "Quiero alquilar una casa en Lima",
    "Busco departamento en Arequipa",
    "Estoy buscando algo en Caballito"
]:
    r = run_chatbot_flow(msg)
    print(f"\nUsuario: {msg}")
    print("Chatbot:", r["respuesta"])
    if r["ids"]:
        print("IDs:", r["ids"])
