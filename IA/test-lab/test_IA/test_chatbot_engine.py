from app.services.chatbot_engine import proccess_chat_turn

user_id = "test123"
conv_id = "conv123"
mensaje = "deseo una casa de alquiler en lima cerca de un río con 3 cuartos"

respuesta = proccess_chat_turn(user_id, conv_id, mensaje)

print("🧠 Respuesta del chatbot:\n")
print(respuesta)
